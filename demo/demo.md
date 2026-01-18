# Running Fixtrace Demo (Docker Port Conflict)

## 1. Start a process in one terminal that uses port 5432
```bash
python3 -m http.server 5432
```

## 2a. In another terminal, start Fixtrace

```bash
fixtrace start
```

## 2b. Go to the directory of docker-compose.yaml and run Docker Compose

```bash
cd path/to/your/docker-files
docker compose up
```

## 3. Expected Error if port 5432 is in use
```bash
Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:5432 -> 127.0.0.1:0: listen tcp 0.0.0.0:5432: bind: address already in use
```

## 4. Solution to fix conflict 

```bash
lsof -i :5432
kill <PID> 
docker compose up
```




