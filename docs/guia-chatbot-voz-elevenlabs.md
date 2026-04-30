# Guia: Chatbot de voz con ElevenLabs + Flask

## 1) Arquitectura recomendada
- **Frontend web**: captura microfono con Web Speech API o MediaRecorder.
- **Backend Flask**: endpoint `/api/chat` para enviar texto a un LLM y devolver respuesta.
- **TTS**: ElevenLabs convierte la respuesta en audio reproducible.
- **(Opcional) STT**: Whisper/API para transcribir audio del usuario.

## 2) Flujo basico
1. Usuario habla.
2. Se transcribe a texto.
3. Se envia al backend.
4. El backend genera respuesta (OpenAI u otro).
5. ElevenLabs sintetiza voz.
6. El navegador reproduce el MP3.

## 3) Variables de entorno
```env
ELEVENLABS_API_KEY=tu_api_key
ELEVENLABS_VOICE_ID=voz_id
OPENAI_API_KEY=tu_api_key
```

## 4) Endpoint de ejemplo (Flask)
```python
@app.post('/api/chat')
def chat():
    user_text = request.json.get('message', '')
    respuesta = generar_respuesta_llm(user_text)
    audio_bytes = sintetizar_elevenlabs(respuesta)
    return send_file(io.BytesIO(audio_bytes), mimetype='audio/mpeg')
```

## 5) Control de creditos en ElevenLabs
- Usa voces cortas para pruebas iniciales.
- Limita longitud de respuesta (ej. 200 caracteres).
- Cachea respuestas frecuentes (saludos, ayuda, FAQ).
- Activa fallback a texto cuando no haya creditos.

## 6) Siguiente paso en esta plataforma
- Integrar boton "Hablar con Coach IA" en `usuario/dashboard.html`.
- Mostrar tips deportivos personalizados segun metricas del usuario.
