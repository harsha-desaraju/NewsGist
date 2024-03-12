
import gradio as gr
from utils import getNews




if __name__ == '__main__':

    # Create the a simple web interface
    demo = gr.Interface(
        fn = getNews,
        inputs = ['text'],
        outputs = ['text'],
    )

    demo.launch()