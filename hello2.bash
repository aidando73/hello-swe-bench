# Setup environment - https://github.com/swe-bench/SWE-bench/blob/5f5a7df799663adba4b191eca3d675faf3621fe2/swebench/harness/constants.py#L208-L218
cd /Users/aidand/dev/hello-swe-bench/django
source ~/miniconda3/bin/activate
conda create --prefix ./env python=3.11 -y
conda activate ./env
python -m pip install -e .
# python -m pip install -r requirements.txt
