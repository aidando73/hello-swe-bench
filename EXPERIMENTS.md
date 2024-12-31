```bash
mkdir -p logs/evals
https://github.com/django/django.git

mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

(cd django && source ~/miniconda3/bin/activate && conda create --prefix ./env_3_8 python=3.8)
(cd django && source ~/miniconda3/bin/activate && conda create --prefix ./env_3_9 python=3.9)
(cd django && source ~/miniconda3/bin/activate && conda create --prefix ./env_3_11 python=3.11)

log_file=full_eval_$(date +%Y-%m-%d_%H-%M).log && \
touch logs/evals/$(date "+%Y-%m-%d_%H:%M").log && \
python eval6.py  2>&1 | \
stdbuf -o0 tee -a logs/$log_file
```

### Run v12

- 58 instances
- Llama 3.3 70B
- 30 max iterations on each instance
- Rough cost estimate: $150