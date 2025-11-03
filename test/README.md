- to test the script:
  create `.env` file in the root folder of the project:

```env
GITHUB_WORKSPACE=test
DEPLOYMENT_FILE=forge-deploy.test.yml
FORGE_API_TOKEN=<your-token>
```

then run:

```bash
python src/main.py
```

- to test action
  create a `.secrets` file in `test` directory, with a forge api token ex: `FORGE_API_TOKEN=your-token` then:

```bash
cd test
act
```

**note**: you need to install act first, refer to [act](https://github.com/nektos/act)
