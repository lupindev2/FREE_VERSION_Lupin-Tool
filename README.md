<div align="center">

<img src="assets/background/image.png" alt="Lupin Tool" width="100%">

# LUPIN TOOL

![Python](https://img.shields.io/badge/Python-3-black?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/Interface-PySide6-black?style=for-the-badge)
![Pygame](https://img.shields.io/badge/UI-Pygame-black?style=for-the-badge)
![Windows](https://img.shields.io/badge/Plateforme-Windows-black?style=for-the-badge&logo=windows&logoColor=white)

</div>

---

## Utilisation

1. Téléchargez le dépôt en ZIP et extrayez le dossier.
2. Installez Python 3 (`python` et `pip` doivent être disponibles dans un terminal).
3. Renseignez vos identifiants ScrapHub dans `settings/options/.env` (copiez `.env.example`).
4. Double-cliquez sur `start.bat`.

Ou depuis PowerShell, dans le dossier du projet :

```powershell
python -m pip install --user -r requirements.txt
python start.py
```

## Configuration ScrapHub

Placez votre e-mail et mot de passe ScrapHub dans `settings/options/.env`.
Sans identifiants, la page de recherche vous indiquera de contacter
`lupinducoup` sur Discord.

- Ne partagez jamais votre `.env` ni votre mot de passe.
- Le `.env` est ignoré par Git ; seul `.env.example` est dans le dépôt.
- Utilisez uniquement des identifiants que vous êtes autorisé à utiliser.

## Vidéos et médias

Les vidéos sont dans `assets/videos` (le tableau utilise `videoB2.mp4`).
La musique et l'image d'ambiance sont dans `assets/songs` et `assets/background`.
Conservez cette structure de dossiers après extraction.

## Dépannage

- **Connexion ScrapHub** : vérifiez Internet et les identifiants du `.env`.
  Si une autre URL API vous a été donnée, ajoutez `SCRAPHUB_API_URL` dans ce fichier.
- **« Identifiants ScrapHub absents »** : renseignez `SCRAPHUB_EMAIL` et
  `SCRAPHUB_PASSWORD` dans `settings/options/.env`.
- **Intro vidéo absente** : vérifiez que `assets/videos` contient bien les fichiers.
  Sans vidéo, l'application démarre directement sur le menu.
- **Dépendances ou démarrage** : relancez `start.bat` ou
  `python -m pip install --user -r requirements.txt`.

## Contact

Une question ou un problème : **`lupinducoup` sur Discord**.
N'envoyez jamais votre `.env`, mot de passe, jeton ou capture contenant des identifiants.

---

<div align="center">

**LUPIN TOOL**

</div>