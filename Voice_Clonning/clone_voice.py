from gradio_client import Client, handle_file
import shutil

TEXT = "Hello, this is my cloned voice speaking."

client = Client("mrfakename/MegaTTS3-Voice-Cloning")
result = client.predict(
    inp_audio=handle_file("sample.mp3"),
    inp_text=TEXT,
    infer_timestep=32,
    p_w=1.4,
    t_w=3.0,
    api_name="/generate_speech"
)
shutil.copy(result, "output.mp3")
print("Saved output.mp3")
