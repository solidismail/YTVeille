# YTVeille — Veille automatique YouTube en français

Veille automatique des meilleures vidéos YouTube **en français** sur n'importe quel domaine technique.
Requêtes configurables dynamiquement, scoring multi-critères, dark mode, filtres avancés.

---

## Prérequis

- Docker & Docker Compose
- [Clé YouTube Data API v3](https://console.cloud.google.com/)

---

## Démarrage rapide (local)

```bash
# 1. Cloner le projet
git clone https://github.com/TON_USER/YTVeille.git
cd YTVeille

# 2. Configurer les variables d'environnement
cp .env.example .env
# Puis éditer .env et remplacer "your_youtube_data_api_v3_key_here" par ta clé
# NEXT_PUBLIC_API_URL reste http://localhost:8000 pour un usage local

# 3. Lancer les services
docker compose up -d --build

# 4. Ouvrir l'application
# Frontend : http://localhost:3000
# API docs : http://localhost:8000/docs
```

Le **worker** effectue une 1ère mise à jour au démarrage, puis quotidiennement à 6h UTC.

---

## Architecture

```
├── backend/
│   ├── api/        FastAPI — REST API, endpoints /videos, /refresh, /status, /config
│   ├── scoring/    Algorithme de scoring multi-critères (sur 100)
│   └── worker/     APScheduler — cron quotidien + pipeline fetch→score→persist
├── frontend/       Next.js 14 — Dashboard UI (filtres + cards + dark mode)
├── data/           videos.json, config.json, quota_status.json (volume Docker partagé)
└── docker-compose.yml
```

---

## Score des vidéos (0–100)

| Critère | Poids |
|---|---|
| Vues pondérées par ancienneté | 25 pts |
| Ratio likes / vues | 20 pts |
| Mots-clés techniques détectés | 25 pts |
| Durée ≥ 10 min | 10 pts |
| Présence de chapitrage | 10 pts |
| Nombre de topics distincts | 10 pts |

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `YOUTUBE_API_KEY` | Clé YouTube Data API v3 (obligatoire) |
| `DATA_PATH` | Chemin du fichier JSON (défaut : `/app/data/videos.json`) |
| `NEXT_PUBLIC_API_URL` | URL publique de l'API appelée par le navigateur (défaut : `http://localhost:8000`) |

> **Important** : `NEXT_PUBLIC_API_URL` est compilée dans le bundle JavaScript au moment du `docker build`.
> Elle doit pointer vers l'IP/domaine **public** du serveur, pas le hostname Docker interne.

---

## Commandes utiles

```bash
# Voir les logs en temps réel
docker compose logs -f

# Forcer une mise à jour manuelle
curl -X POST http://localhost:8000/api/refresh

# Voir le statut de l'API (quota, vidéos, refresh en cours)
curl http://localhost:8000/api/status | jq .

# Lancer les tests unitaires (backend)
cd backend && pip install -e ".[dev]" && pytest scoring/tests/ -v
```

---

## Guide de déploiement sur un serveur distant

### 1. Provisionner un VPS

N'importe quel fournisseur : **OVH** (~3€/mois), Hetzner, DigitalOcean, AWS EC2...
OS recommandé : **Ubuntu 22.04 LTS**

### 2. Installer Docker sur le serveur

```bash
# Se connecter en SSH
ssh user@TON_IP_SERVEUR

# Installer Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Déconnecte-toi et reconnecte-toi pour appliquer le groupe
exit
ssh user@TON_IP_SERVEUR
```

### 3. Copier le projet sur le serveur

**Option A — via Git (recommandé) :**
```bash
# Sur le serveur
git clone https://github.com/TON_USER/YTVeille.git
cd YTVeille
```

**Option B — via rsync depuis ta machine locale :**
```bash
# Depuis ta machine locale
rsync -av --exclude='node_modules' --exclude='.next' --exclude='data' \
  /chemin/local/YTVeille/ \
  user@TON_IP_SERVEUR:~/YTVeille/
```

### 4. Créer le fichier `.env` sur le serveur

```bash
# Sur le serveur, dans le dossier YTVeille/
cat > .env << 'EOF'
YOUTUBE_API_KEY=ta_cle_youtube_api
NEXT_PUBLIC_API_URL=http://TON_IP_SERVEUR:8000
EOF
```

> `NEXT_PUBLIC_API_URL` doit être l'IP ou le domaine **public** du serveur sur le port 8000,
> car c'est le navigateur du visiteur qui appelle l'API directement.

### 5. Ouvrir les ports du pare-feu

```bash
sudo ufw allow 22    # SSH
sudo ufw allow 3000  # Frontend
sudo ufw allow 8000  # API
sudo ufw enable
```

### 6. Lancer l'application

```bash
cd ~/YTVeille
docker compose up -d --build
docker compose ps    # vérifier que tout tourne
```

L'application est accessible sur `http://TON_IP_SERVEUR:3000`

### 7. (Optionnel) Domaine + HTTPS avec nginx

Si tu as un nom de domaine (ex: `ytveille.monsite.com`) :

**Installer nginx et certbot :**
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

**Créer la configuration nginx** (`/etc/nginx/sites-available/ytveille`) :
```nginx
server {
    server_name ytveille.monsite.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Activer et sécuriser :**
```bash
sudo ln -s /etc/nginx/sites-available/ytveille /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Générer le certificat SSL (HTTPS gratuit)
sudo certbot --nginx -d ytveille.monsite.com
```

**Mettre à jour le `.env`** avec l'URL HTTPS :
```bash
# Modifier NEXT_PUBLIC_API_URL pour utiliser le domaine
NEXT_PUBLIC_API_URL=https://ytveille.monsite.com

# Puis rebuilder le frontend
docker compose up -d --build frontend
```

> Avec nginx, les ports 3000 et 8000 ne sont plus exposés directement :
> tout passe par le port 443 (HTTPS) via le reverse proxy.

---

## Quota YouTube API

L'API YouTube Data v3 est limitée à **10 000 unités/jour** (chaque recherche coûte 100 unités,
soit ~100 recherches max). En cas de dépassement :

- Un banner d'avertissement s'affiche automatiquement dans l'application
- Le quota se renouvelle chaque jour à **minuit heure du Pacifique** (~8h–9h UTC)
- Pour obtenir plus de quota : [console.cloud.google.com](https://console.cloud.google.com) → API & Services → Quotas
