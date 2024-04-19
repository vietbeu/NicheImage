apt-get update && apt install -y byobu && \
python -m venv mainenv && . mainenv/bin/activate && pip install -e . && \
python -m venv vllm && . vllm/bin/activate && pip install vllm && \
. generation_models/comfyui_helper/install_comfyui.sh && . generation_models/comfyui_helper/scripts/download_antelopev2.sh && \
mkdir -p ~/miniconda3 && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh && \
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 && \
    rm -rf ~/miniconda3/miniconda.sh && ~/miniconda3/bin/conda init bash && \

. generation_models/comfyui_helper/install_comfyui.sh && . generation_models/comfyui_helper/scripts/download_antelopev2.sh