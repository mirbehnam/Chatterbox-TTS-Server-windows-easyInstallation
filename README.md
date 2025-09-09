# 🌍 Multilingual Chatterbox TTS Server (Windows Edition)

Enhanced [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) server with **multilingual support** and **easy Windows installation**. Generate high-quality speech in 24+ languages with voice cloning capabilities.

## 📺 Video Tutorials

- **Setup Guide:** [**How to in 1 minute - YouTube**](https://www.youtube.com/@Howto_in_1_minute)
- **Full Tutorial:** [Complete Walkthrough](https://www.youtube.com/@Howto_in_1_minute)

## ✨ Key Features

🌐 **24+ Languages:** Arabic, Chinese, Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Italian, Japanese, Korean, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swedish, Swahili, Turkish

🎤 **Voice Cloning:** Clone any voice using reference audio files

📚 **Audiobook Generation:** Process entire books with automatic text chunking

🚀 **Easy Windows Installation:** One-click setup with `install.bat`

⚡ **GPU Acceleration:** NVIDIA (CUDA) and AMD (ROCm) support

🌐 **Modern Web UI:** Intuitive interface with real-time audio playback

📡 **FastAPI Server:** RESTful API with interactive documentation

## 🖥️ Platform Support

- **Windows:** Full support with easy installation script
- **Linux:** Manual installation supported  
- **macOS:** Use the [main repository](https://github.com/devnen/Chatterbox-TTS-Server)

## 🔩 System Requirements

- **Windows 10/11** (64-bit) or **Linux**
- **Python 3.10+**
- **4GB+ RAM** (8GB+ recommended)
- **5GB+ storage** for models
- **GPU (Optional):** NVIDIA with 4GB+ VRAM or AMD RX 6000/7000 series

## 🚀 Quick Installation (Windows)

1. **Download**
   ```bash
   git clone https://github.com/mirbehnam/Chatterbox-TTS-Server-windows-easyInstallation.git
   cd Chatterbox-TTS-Server
   ```

2. **Install**
   - Double-click `install.bat`
   - Choose your hardware:
     - Option 1: NVIDIA GPU (CUDA)
     - Option 2: CPU Only
     - Option 3: AMD GPU (ROCm)

3. **Run**
   - Double-click `win-run.bat`

4. **Access**
   - Open `http://localhost:8004` in your browser

## 💻 Manual Installation (Linux/Other)

1. **Clone Repository**
   ```bash
   git clone https://github.com/mirbehnam/Chatterbox-TTS-Server-windows-easyInstallation.git
   cd Chatterbox-TTS-Server
   ```

2. **Setup Environment**
   > **Note:** Make sure you're using Python 3.10 for compatibility
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

3. **Install Dependencies**
   
   Choose based on hardware:
   ```bash
   # NVIDIA GPU
   pip install -r requirements-nvidia.txt
   
   # AMD GPU  
   pip install -r requirements-rocm.txt
   
   # CPU Only
   pip install -r requirements.txt
   ```

4. **Run Server**
   ```bash
   source venv/bin/activate  # if not already activated
   python server.py
   ```

## ▶️ Running the Application

**Windows:** Double-click `win-run.bat`

**Linux/Manual:** 
```bash
source venv/bin/activate
python server.py
```

**Access:** Open `http://localhost:8004`

**API Docs:** Visit `http://localhost:8004/docs`

## 🎯 Usage

### Web Interface
1. Enter text in any supported language
2. Select target language from dropdown
3. Choose voice mode (predefined or clone)
4. Adjust generation settings
5. Generate and listen to speech

### API Examples

**Main TTS Endpoint:**
```bash
POST /tts
{
  "text": "Hello world!",
  "language": "en", 
  "voice_mode": "predefined",
  "temperature": 0.7,
  "speed_factor": 1.0
}
```

**OpenAI Compatible:**
```bash
POST /v1/audio/speech
{
  "input": "Your text here",
  "voice": "S1",
  "language": "en",
  "response_format": "wav"
}
```

## 🎤 Voice Management

**Predefined Voices:** Place `.wav`/`.mp3` files in `./voices` directory

**Voice Cloning:** Upload reference audio via Web UI (stored in `./reference_audio`)

## ⚙️ Configuration

Edit `config.yaml` for settings:
```yaml
server:
  host: "0.0.0.0"
  port: 8004

tts_engine:
  device: "auto"  # auto, cuda, cpu
  
generation_defaults:
  temperature: 0.7
  language: "en"
```



## 🔍 Troubleshooting

For comprehensive troubleshooting, visit the [main repository](https://github.com/devnen/Chatterbox-TTS-Server).

**Common Issues:**
- GPU not detected: Verify drivers and restart
- Import errors: Ensure virtual environment is activated  
- Port conflicts: Change port in `config.yaml`

## 🤝 Contributing

Contributions welcome! Report bugs, suggest features, or submit pull requests.

## 📜 License

MIT License

## 🙏 Acknowledgements

- [Resemble AI](https://www.resemble.ai/) for [Chatterbox TTS](https://github.com/resemble-ai/chatterbox)
- [devnen](https://github.com/devnen) for the original [server implementation](https://github.com/devnen/Chatterbox-TTS-Server)

## 📞 Support

- **General Issues:** [Main repository](https://github.com/devnen/Chatterbox-TTS-Server)
- **Windows Issues:** Open issue in this repository
- **macOS Users:** Use [main repository](https://github.com/devnen/Chatterbox-TTS-Server)
- **Video Tutorials:** [**How to in 1 minute - YouTube**](https://www.youtube.com/@Howto_in_1_minute)

---

*Generate speech in 24+ languages with one-click Windows installation!*