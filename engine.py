# File: engine.py
# Core TTS model loading and speech generation logic.
import os
os.environ["TRANSFORMERS_ATTN_IMPLEMENTATION"] = "eager"
import logging
import random
import numpy as np
import torch
import gc
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from typing import Optional, Tuple
from pathlib import Path
from chatterbox.tts import ChatterboxTTS  # Main TTS engine class
from chatterbox.models.s3gen.const import (
    S3GEN_SR,
)  # Default sample rate from the engine

# Import the singleton config_manager
from config import config_manager

logger = logging.getLogger(__name__)



from pathlib import Path
import torch
from safetensors.torch import load_file as load_safetensors

from chatterbox.models.t3 import T3
from chatterbox.models.t3.modules.t3_config import T3Config
from chatterbox.models.s3gen import S3Gen
from chatterbox.models.voice_encoder import VoiceEncoder
from chatterbox.models.tokenizers import MTLTokenizer
from chatterbox.mtl_tts import Conditionals, SUPPORTED_LANGUAGES # Need to import these too

class PatchedChatterboxTTS(ChatterboxMultilingualTTS):
    """
    An inherited class that fixes the attention implementation issue by overriding
    the `from_local` class method.
    """
    @classmethod
    def from_local(cls, ckpt_dir, device) -> 'PatchedChatterboxTTS':
        print("🚀 Using PatchedChatterboxTTS.from_local to load the model.")
        ckpt_dir = Path(ckpt_dir)

        # --- This is the original code from the library ---
        ve = VoiceEncoder()
        ve.load_state_dict(
            torch.load(ckpt_dir / "ve.pt", weights_only=True)
        )
        ve.to(device).eval()
        
        # --- OUR FIX IS APPLIED HERE ---
        # 1. Create the T3Config
        t3_config = T3Config.multilingual()
        
        # 2. Patch the config object directly
        # This part is slightly different because T3 doesn't take the config directly for attn
        # We'll go back to patching the LlamaConfig inside T3's init, but called from our override
        
        # Let's use the better approach of patching the T3's config logic
        # For simplicity, we directly recreate the T3 object with the fix logic
        from chatterbox.models.t3.llama_configs import LLAMA_CONFIGS
        from transformers import LlamaConfig, LlamaModel
        
        hp = T3Config.multilingual()
        cfg = LlamaConfig(**LLAMA_CONFIGS[hp.llama_config_name])
        cfg._attn_implementation = "eager" # Our patch
        
        # We need to manually recreate T3 since we can't inject the patched cfg easily
        # A simpler way is to just call the original method and then fix the model...
        # Let's try a cleaner override. We will replicate the method entirely.

        # The T3 class init needs to be fixed. So we create our own T3.
        class PatchedT3(T3):
            def __init__(self, hp=None):
                super().__init__(hp)
                # Override the transformer model with a patched config
                cfg = self.cfg
                cfg._attn_implementation = "eager"
                self.tfmr = LlamaModel(cfg)

        t3 = PatchedT3(T3Config.multilingual()) # Use our patched T3
        
        t3_state = load_safetensors(ckpt_dir / "t3_23lang.safetensors")
        if "model" in t3_state.keys():
            t3_state = t3_state["model"][0]
        t3.load_state_dict(t3_state)
        t3.to(device).eval()

        s3gen = S3Gen()
        s3gen.load_state_dict(
            torch.load(ckpt_dir / "s3gen.pt", weights_only=True)
        )
        s3gen.to(device).eval()

        tokenizer = MTLTokenizer(
            str(ckpt_dir / "mtl_tokenizer.json")
        )

        conds = None
        if (builtin_voice := ckpt_dir / "conds.pt").exists():
            conds = Conditionals.load(builtin_voice).to(device)

        return cls(t3, s3gen, ve, tokenizer, device, conds=conds)


# --- Global Module Variables ---
multilingual_model: Optional[PatchedChatterboxTTS] = None
MULTILINGUAL_MODEL_LOADED: bool = False
chatterbox_model: Optional[ChatterboxTTS] = None
MODEL_LOADED: bool = False
model_device: Optional[str] = (
    None  # Stores the resolved device string ('cuda' or 'cpu')
)


def set_seed(seed_value: int):
    """
    Sets the seed for torch, random, and numpy for reproducibility.
    This is called if a non-zero seed is provided for generation.
    """
    torch.manual_seed(seed_value)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)  # if using multi-GPU
    if torch.backends.mps.is_available():
        torch.mps.manual_seed(seed_value)
    random.seed(seed_value)
    np.random.seed(seed_value)
    logger.info(f"Global seed set to: {seed_value}")


def _test_cuda_functionality() -> bool:
    """
    Tests if CUDA is actually functional, not just available.

    Returns:
        bool: True if CUDA works, False otherwise.
    """
    if not torch.cuda.is_available():
        return False

    try:
        test_tensor = torch.tensor([1.0])
        test_tensor = test_tensor.cuda()
        test_tensor = test_tensor.cpu()
        return True
    except Exception as e:
        logger.warning(f"CUDA functionality test failed: {e}")
        return False


def _test_mps_functionality() -> bool:
    """
    Tests if MPS is actually functional, not just available.

    Returns:
        bool: True if MPS works, False otherwise.
    """
    if not torch.backends.mps.is_available():
        return False

    try:
        test_tensor = torch.tensor([1.0])
        test_tensor = test_tensor.to("mps")
        test_tensor = test_tensor.cpu()
        return True
    except Exception as e:
        logger.warning(f"MPS functionality test failed: {e}")
        return False


def load_model() -> bool:
    """
    Loads the TTS model.
    This version directly attempts to load from the Hugging Face repository (or its cache)
    using `from_pretrained`, bypassing the local `paths.model_cache` directory.
    Updates global variables `chatterbox_model`, `MODEL_LOADED`, and `model_device`.

    Returns:
        bool: True if the model was loaded successfully, False otherwise.
    """
    global chatterbox_model, MODEL_LOADED, model_device

    if MODEL_LOADED:
        logger.info("TTS model is already loaded.")
        return True

    try:
        # Determine processing device with robust CUDA detection and intelligent fallback
        device_setting = config_manager.get_string("tts_engine.device", "auto")

        if device_setting == "auto":
            if _test_cuda_functionality():
                resolved_device_str = "cuda"
                logger.info("CUDA functionality test passed. Using CUDA.")
            elif _test_mps_functionality():
                resolved_device_str = "mps"
                logger.info("MPS functionality test passed. Using MPS.")
            else:
                resolved_device_str = "cpu"
                logger.info("CUDA and MPS not functional or not available. Using CPU.")

        elif device_setting == "cuda":
            if _test_cuda_functionality():
                resolved_device_str = "cuda"
                logger.info("CUDA requested and functional. Using CUDA.")
            else:
                resolved_device_str = "cpu"
                logger.warning(
                    "CUDA was requested in config but functionality test failed. "
                    "PyTorch may not be compiled with CUDA support. "
                    "Automatically falling back to CPU."
                )

        elif device_setting == "mps":
            if _test_mps_functionality():
                resolved_device_str = "mps"
                logger.info("MPS requested and functional. Using MPS.")
            else:
                resolved_device_str = "cpu"
                logger.warning(
                    "MPS was requested in config but functionality test failed. "
                    "PyTorch may not be compiled with MPS support. "
                    "Automatically falling back to CPU."
                )

        elif device_setting == "cpu":
            resolved_device_str = "cpu"
            logger.info("CPU device explicitly requested in config. Using CPU.")

        else:
            logger.warning(
                f"Invalid device setting '{device_setting}' in config. "
                f"Defaulting to auto-detection."
            )
            if _test_cuda_functionality():
                resolved_device_str = "cuda"
            elif _test_mps_functionality():
                resolved_device_str = "mps"
            else:
                resolved_device_str = "cpu"
            logger.info(f"Auto-detection resolved to: {resolved_device_str}")

        model_device = resolved_device_str
        logger.info(f"Final device selection: {model_device}")

        # Get configured model_repo_id for logging and context,
        # though from_pretrained might use its own internal default if not overridden.
        model_repo_id_config = config_manager.get_string(
            "model.repo_id", "ResembleAI/chatterbox"
        )

        logger.info(
            f"Attempting to load model directly using from_pretrained (expected from Hugging Face repository: {model_repo_id_config} or library default)."
        )
        try:
            # Directly use from_pretrained. This will utilize the standard Hugging Face cache.
            # The ChatterboxTTS.from_pretrained method handles downloading if the model is not in the cache.
           
           
            chatterbox_model = ChatterboxTTS.from_pretrained(device=model_device)

           
            # The actual repo ID used by from_pretrained is often internal to the library,
            # but logging the configured one provides user context.
            logger.info(
                f"Successfully loaded TTS model using from_pretrained on {model_device} (expected from '{model_repo_id_config}' or library default)."
            )
        except Exception as e_hf:
            logger.error(
                f"Failed to load model using from_pretrained (expected from '{model_repo_id_config}' or library default): {e_hf}",
                exc_info=True,
            )
            chatterbox_model = None
            MODEL_LOADED = False
            return False

        MODEL_LOADED = True
        if chatterbox_model:
            logger.info(
                f"TTS Model loaded successfully on {model_device}. Engine sample rate: {chatterbox_model.sr} Hz."
            )
        else:
            logger.error(
                "Model loading sequence completed, but chatterbox_model is None. This indicates an unexpected issue."
            )
            MODEL_LOADED = False
            return False

        return True

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during model loading: {e}", exc_info=True
        )
        chatterbox_model = None
        MODEL_LOADED = False
        return False

def load_multilingual_model() -> bool:
    """
    Loads the multilingual TTS model, unloads the standard model,
    and sets the multilingual model as the default for all languages.
    """
    global multilingual_model, MULTILINGUAL_MODEL_LOADED, model_device
    global chatterbox_model, MODEL_LOADED

    if MULTILINGUAL_MODEL_LOADED:
        logger.info("Multilingual TTS model is already loaded and set as default.")
        return True

    if model_device is None:
        logger.error("Main model device not determined. Load main model first.")
        return False

    # --- مرحله کلیدی: خالی کردن مدل استاندارد از حافظه ---
    if chatterbox_model is not None:
        logger.info("Unloading the standard ChatterboxTTS model to free up memory...")
        chatterbox_model = None
        MODEL_LOADED = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect() # اجرای сборщик мусора
        logger.info("Standard model unloaded and memory cleared.")

    try:
        logger.info(f"Loading multilingual model (PatchedChatterboxTTS) on {model_device}...")

        # مدل چندزبانه را بارگذاری کنید
        multilingual_model = PatchedChatterboxTTS.from_pretrained(device=model_device)
        
        # --- مرحله کلیدی: جایگزینی مدل اصلی با مدل چندزبانه ---
        # حالا مدل چندزبانه را به عنوان مدل اصلی (chatterbox_model) تنظیم می کنیم
        # تا تمام درخواست ها، حتی انگلیسی، از این مدل استفاده کنند.
        chatterbox_model = multilingual_model
        
        # هر دو فلگ را True قرار می دهیم تا سیستم بداند مدل آماده است
        MULTILINGUAL_MODEL_LOADED = True
        MODEL_LOADED = True # <-- این مهم است

        logger.info(f"PatchedChatterboxTTS model loaded successfully on {model_device}.")
        logger.info("This model will now be used for ALL languages, including English.")
        return True

    except Exception as e:
        logger.error(f"Error loading multilingual model: {e}", exc_info=True)
        multilingual_model = None
        chatterbox_model = None
        MULTILINGUAL_MODEL_LOADED = False
        MODEL_LOADED = False
        return False
    
def synthesize(
    text: str,
    audio_prompt_path: Optional[str] = None,
    temperature: float = 0.8,
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5,
    seed: int = 0,
    language: str = "en",
) -> Tuple[Optional[torch.Tensor], Optional[int]]:
    """
    Synthesizes audio from text using the currently loaded TTS model.
    If the multilingual model is loaded, it handles all languages.
    """
    global chatterbox_model, multilingual_model # متغیرها برای وضوح اینجا هستند

    # از آنجایی که پس از بارگذاری مدل چندزبانه، chatterbox_model به آن اشاره می کند،
    # دیگر نیازی به بررسی جداگانه نیست.
    if not MODEL_LOADED or chatterbox_model is None:
        logger.error("TTS model is not loaded. Cannot synthesize audio.")
        return None, None
    
    # مدل فعال همیشه chatterbox_model خواهد بود
    active_model = chatterbox_model

    try:
        if seed != 0:
            logger.info(f"Applying user-provided seed for generation: {seed}")
            set_seed(seed)
        else:
            logger.info("Using default (potentially random) generation behavior as seed is 0.")

        logger.debug(
            f"Synthesizing with params: audio_prompt='{audio_prompt_path}', temp={temperature}, "
            f"exag={exaggeration}, cfg_weight={cfg_weight}, seed_applied_globally_if_nonzero={seed}, "
            f"language={language}"
        )

        # بررسی می کنیم که آیا مدل بارگذاری شده از نوع چندزبانه است یا نه
        is_multilingual = isinstance(active_model, ChatterboxMultilingualTTS)
        
        if is_multilingual:
            # اگر مدل چندزبانه است، پارامتر language_id را ارسال می کنیم
            logger.info(f"Synthesizing with multilingual model for language: {language}")
            wav_tensor = active_model.generate(
                text=text,
                audio_prompt_path=audio_prompt_path,
                temperature=temperature,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                language_id=language, # <-- پارامتر زبان
            )
        else:
            # اگر به هر دلیلی مدل استاندارد بارگذاری شده باشد (مثلاً قبل از فراخوانی load_multilingual_model)
            logger.info("Synthesizing with standard English model.")
            wav_tensor = active_model.generate(
                text=text,
                audio_prompt_path=audio_prompt_path,
                temperature=temperature,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
            )

        return wav_tensor, active_model.sr

    except Exception as e:
        logger.error(f"Error during TTS synthesis: {e}", exc_info=True)
        return None, None