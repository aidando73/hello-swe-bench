
- Go to https://github.com/settings/personal-access-tokens/new
  - Fill in name
  - Select repositories you want it to have access to
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

