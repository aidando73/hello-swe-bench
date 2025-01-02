
- Go to https://github.com/settings/personal-access-tokens/new
  - Fill in name
  - Select the repositories you want it to have access to
![alt text](image.png)
- Add TODO permissions

![alt text](image-1.png)

Copy the .env.example file to .env

```bash
cp .env.example .env
```

- Add your github token to the .env file

```bash
GITHUB_TOKEN=github_pat_11SDF...
```

- This only supports 3.3 70B model at the moment

Run a llama-stack distribution, we use fireworks in this example, but you can use any other distribution that supports the 3.3 70B model:
```bash
# Run a llama-stack distribution
export LLAMA_STACK_PORT=5000
# You can get an api key from https://fireworks.ai/account/api-keys
export FIREWORKS_API_KEY=__your_fireworks_api_key_here__
docker run -it \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ~/.llama:/root/.llama \
  llamastack/distribution-fireworks \
  --port $LLAMA_STACK_PORT \
  --env FIREWORKS_API_KEY=$FIREWORKS_API_KEY
```

- Run the agent, giving it the issue number or url you want solved

```bash
python3 agent.py 
```