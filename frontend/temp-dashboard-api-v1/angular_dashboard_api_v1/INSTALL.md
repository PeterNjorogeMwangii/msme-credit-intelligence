# Dashboard live API package

Copy `src` into the Angular `src` folder and copy `proxy.conf.json` into the Angular project root.

Run Angular with:

```powershell
npm start -- --proxy-config proxy.conf.json
```

FastAPI must be running at `http://127.0.0.1:8000`.
