# ⚙️ Settings Area - Complete Guide

## 🎯 Overview

The Settings area provides a comprehensive interface to configure your AI models, providers, and generation parameters. Access it via the **⚙️ Settings** tab in the web interface.

## 📍 Access

1. Open your browser: **http://localhost:8501**
2. Click the **"⚙️ Settings"** tab (3rd tab from left)

## 🔧 Features

### 1️⃣ Provider Selection

Choose between two AI providers:

- **🏠 Ollama** (Local)
  - Runs on your machine
  - Free to use
  - No API key needed
  - Requires Ollama to be running (`ollama serve`)

- **☁️ OpenRouter** (Cloud)
  - Cloud-based models
  - Requires API key (get from https://openrouter.ai/keys)
  - Access to many models including GPT-4, Claude, etc.

### 2️⃣ Model Discovery

**Fetch Available Models Button** (🔍)

**For Ollama:**
```
1. Ensure Ollama is running (ollama serve)
2. Click "🔍 Fetch Available Models"
3. System queries http://localhost:11434/api/tags
4. Displays all locally installed models
```

**For OpenRouter:**
```
1. Enter your API key in the "OpenRouter API Key" field
2. Click "🔍 Fetch Available Models"
3. System queries https://openrouter.ai/api/v1/models
4. Displays all available cloud models
```

### 3️⃣ Model Configuration

**Ollama Configuration:**
- **Base URL**: Where Ollama is running (default: http://localhost:11434/v1)
- **Primary Model**: Main model for generation (e.g., gpt-oss:20b-cloud)
- **Fallback Model**: Backup model if rate limited (e.g., qwen3:1.7B)
- **Temperature**: 0.0 (deterministic) to 2.0 (creative)
- **Max Tokens**: Response length (256-8192)

**OpenRouter Configuration:**
- **Base URL**: https://openrouter.ai/api/v1
- **Primary Model**: Model ID (e.g., google/gemma-2-9b-it:free)
- **API Key**: Your OpenRouter API key (hidden with password field)
- **Temperature**: 0.0 to 2.0
- **Max Tokens**: 256-8192

### 4️⃣ Advanced Settings (Expandable)

**Agent-Specific Temperature Overrides**

Fine-tune each agent's creativity:

| Agent | Purpose | Default Temp | Recommendation |
|-------|---------|--------------|----------------|
| **Brainstorm** | Outline generation | 0.8 | Higher for creative ideas |
| **Research** | Fact-checking | 0.3 | Lower for accuracy |
| **Content** | Slide content | 0.7 | Balanced |
| **QA** | Quality review | 0.2 | Lowest for consistency |

### 5️⃣ Actions

**💾 Save Configuration**
- Saves all settings to `ai_config.properties`
- Automatically reloads AI configuration
- Changes take effect immediately on next generation
- Shows success message with balloons 🎈

**🔄 Reset to Defaults**
- Clears fetched models list
- Resets form to current file values
- Does not modify the config file

**📋 View Current Configuration**
- Expandable section at bottom
- Shows raw JSON of current settings
- Useful for debugging

## 🎬 Quick Start Guide

### Using Ollama (Recommended for Local)

1. **Ensure Ollama is Running**
   ```bash
   ollama serve
   ```

2. **Open Settings Tab**
   - Go to http://localhost:8501
   - Click "⚙️ Settings"

3. **Select Ollama Provider**
   - Provider dropdown should show "ollama"

4. **Fetch Your Models**
   - Click "🔍 Fetch Available Models"
   - You should see models like: gpt-oss:20b-cloud, qwen3:1.7B, etc.

5. **Choose Models**
   - Primary Model: gpt-oss:20b-cloud (or your preferred large model)
   - Fallback Model: qwen3:1.7B (or a smaller, faster model)

6. **Adjust Settings** (Optional)
   - Temperature: 0.7 (good default)
   - Max Tokens: 2048 (good default)

7. **Save**
   - Click "💾 Save Configuration"
   - Wait for success message

### Using OpenRouter (Cloud)

1. **Get API Key**
   - Go to https://openrouter.ai/keys
   - Create account and generate API key
   - Copy the key (starts with sk-)

2. **Open Settings Tab**
   - Go to http://localhost:8501
   - Click "⚙️ Settings"

3. **Select OpenRouter Provider**
   - Change provider dropdown to "openrouter"

4. **Enter API Key**
   - Paste your API key in the "OpenRouter API Key" field
   - It will be hidden (password field)

5. **Fetch Available Models**
   - Click "🔍 Fetch Available Models"
   - You should see 100+ models including:
     - google/gemma-2-9b-it:free (Free)
     - meta-llama/llama-3.1-8b-instruct:free (Free)
     - openai/gpt-4-turbo (Paid)
     - anthropic/claude-3.5-sonnet (Paid)

6. **Choose Model**
   - Select from dropdown or type model ID
   - Free models are great for testing

7. **Save**
   - Click "💾 Save Configuration"
   - API key is stored securely in config file

## 📊 Configuration File

All settings are saved to: `ai_config.properties`

**Example Configuration:**
```properties
# Provider Selection
ai.provider=ollama

# Ollama Configuration
ollama.base_url=http://localhost:11434/v1
ollama.model=gpt-oss:20b-cloud
ollama.fallback_model=qwen3:1.7B
ollama.temperature=0.7
ollama.max_tokens=2048

# OpenRouter Configuration
openrouter.base_url=https://openrouter.ai/api/v1
openrouter.model=google/gemma-2-9b-it:free
openrouter.api_key=sk-or-v1-...
openrouter.temperature=0.7
openrouter.max_tokens=2048

# Agent Overrides
agent.brainstorm.temperature=0.8
agent.research.temperature=0.3
agent.content.temperature=0.7
agent.qa.temperature=0.2
```

## 🔍 Technical Details

### Model Fetching Functions

**`fetch_ollama_models(base_url)`**
- Connects to Ollama API at `/api/tags`
- Parses response for model names
- Returns: (success: bool, models: List[str], error: str)
- Timeout: 5 seconds

**`fetch_openrouter_models(api_key)`**
- Connects to OpenRouter API at `/models`
- Uses Authorization header with API key
- Returns: (success: bool, models: List[str], error: str)
- Timeout: 10 seconds

### Configuration Management

**`load_config_from_file(config_path)`**
- Reads ai_config.properties
- Parses key=value pairs
- Skips comments and empty lines
- Returns: Dict[str, str]

**`save_config_to_file(config, config_path)`**
- Writes formatted config file
- Preserves all provider settings
- Adds helpful comments
- Ensures proper structure

## 🎨 UI Components

The settings UI uses Streamlit components:
- `st.selectbox()` - Provider and model selection
- `st.text_input()` - URLs, model names, API keys
- `st.slider()` - Temperature controls
- `st.number_input()` - Token limits
- `st.button()` - Actions (fetch, save, reset)
- `st.expander()` - Advanced settings, config view
- `st.columns()` - Layout organization

## ⚠️ Troubleshooting

### "Could not connect to Ollama"
**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### "Invalid API key" (OpenRouter)
**Solution:**
1. Verify key starts with `sk-or-v1-`
2. Check key is valid at https://openrouter.ai/keys
3. Ensure no extra spaces in key

### "Port 8501 is already in use"
**Solution:**
```bash
# Find process using port
netstat -ano | findstr 8501

# Kill old Streamlit process
taskkill /F /PID <process_id>

# Or use different port
streamlit run src/app.py --server.port 8502
```

### Models not showing after fetch
**Solution:**
1. Check browser console for errors (F12)
2. Verify API connectivity
3. Try clicking fetch button again
4. Check session state with "View Current Configuration"

## 🚀 Best Practices

1. **Start with Ollama** if available locally (faster, no API costs)
2. **Use fallback models** for rate limit resilience
3. **Test with free OpenRouter models** before using paid ones
4. **Adjust agent temperatures** based on your use case
5. **Save configuration** after each change
6. **View config** regularly to verify settings

## 📞 Support

If you encounter issues:
1. Check this guide first
2. View "📖 Documentation" tab in app
3. Check logs in `streamlit.log` or `streamlit_new.log`
4. Verify `ai_config.properties` file exists and is readable

## 🎉 Success!

You now have full control over:
- ✅ Model selection (local and cloud)
- ✅ Fallback strategies
- ✅ Temperature tuning per agent
- ✅ Token limits
- ✅ Provider switching

Happy generating! 🎨📊
