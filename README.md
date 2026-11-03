<div align="center">

<img src="assets/background/image.png" alt="Lupin - ambiance nocturne" width="100%">

# LUPIN TOOL

### Une interface d'enquête sombre, pensée pour garder le focus.

![Python](https://img.shields.io/badge/Python-3-black?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/Interface-PySide6-black?style=for-the-badge)
![Pygame](https://img.shields.io/badge/UI-Pygame-black?style=for-the-badge)
![Windows](https://img.shields.io/badge/Plateforme-Windows-black?style=for-the-badge&logo=windows&logoColor=white)

**Interface noire · intro vidéo · musique · outils regroupés au même endroit**

</div>

---

## Présentation

Lupin Tool est une application de bureau Python avec une interface sombre et une
intro vidéo. Selon les modules présents dans cette version, le menu donne accès
à la recherche Scraphub, au tableau d'enquête, à l'ajout de personnes, aux scans,
à l'aide et à Dev Space.

> **Utilisation responsable :** connectez-vous uniquement à des services et
> données auxquels vous êtes autorisé à accéder. Respectez les conditions de
> Scraphub et les lois applicables. Ne partagez pas les informations personnelles
> obtenues par l'application.

## Installation sous Windows

1. Téléchargez le dépôt en ZIP et extrayez entièrement le dossier.
2. Installez Python 3 et assurez-vous que les commandes `python` et `pip` sont
   disponibles dans un terminal.
3. Configurez les identifiants ScrapHub selon la section ci-dessous.
4. Ouvrez le dossier extrait, puis double-cliquez sur `start.bat`.

Le lanceur installe les dépendances de `requirements.txt` pour votre utilisateur,
puis démarre l'application. Vous pouvez aussi lancer depuis PowerShell, dans le
dossier du projet :

```powershell
python -m pip install --user -r requirements.txt
python start.py
```

Pour afficher les options du lanceur :

```powershell
.\start.bat --help
```

## Configuration Scraphub

Pour utiliser la recherche, placez votre e-mail et votre mot de passe ScrapHub
dans `settings/options/.env`. Vous pouvez créer ce fichier en copiant
`.env.example` dans le même dossier. Si les identifiants sont absents, la page
de recherche vous indiquera de contacter `lupinducoup` sur Discord pour obtenir
des identifiants gratuits.

### Garder les identifiants privés

Le `.env` contient des identifiants en texte lisible sur votre ordinateur :

- Ne publiez pas le `.env` et ne partagez pas de mot de passe dans un salon
  public ou un ZIP.
- Le `.env` est ignoré par Git; seul `.env.example`, qui ne contient pas vos
  valeurs, est destiné au dépôt.
- Utilisez uniquement des identifiants que vous êtes autorisé à utiliser.
- Si vous avez déjà partagé un mot de passe ou commité un vrai `.env`, changez
  immédiatement ce mot de passe auprès du service.

Si l'application doit être distribuée à d'autres utilisateurs, ne mettez jamais
un identifiant Scraphub partagé dans le dépôt ou dans le programme. Pour protéger
un secret de service, il faut effectuer les appels sensibles depuis un backend
contrôlé par le propriétaire du service, conserver les secrets uniquement sur ce
backend et authentifier/autoriser chaque utilisateur. Un `.env` côté client
convient uniquement à une configuration locale de confiance.

## Vidéos et médias

Les vidéos d'introduction et du tableau sont incluses dans `assets/videos`.
Conservez cette structure de dossiers après extraction. Le tableau utilise
`videoB2.mp4`; l'introduction lit le premier fichier vidéo compatible trouvé.
Sans vidéo, l'application peut démarrer sans l'introduction.

La musique et l'image d'ambiance se trouvent dans `assets/songs` et
`assets/background`.

## Dépannage

### Problème de connexion Scraphub

Vérifiez votre connexion Internet et les identifiants du `.env`. Si
l'administrateur vous a donné une autre URL API, ajoutez-la avec la variable
`SCRAPHUB_API_URL` dans ce fichier.

### « Identifiants ScrapHub absents »

Renseignez `SCRAPHUB_EMAIL` et `SCRAPHUB_PASSWORD` dans
`settings/options/.env`, ou contactez `lupinducoup` sur Discord pour obtenir
des identifiants gratuits. Ne collez pas vos identifiants dans un message
public pour demander de l'aide.

### L'introduction vidéo ne s'affiche pas

Vérifiez que `assets/videos` est présent après extraction et que les fichiers
vidéo s'y trouvent. L'introduction passe au menu si la vidéo est absente ou si
Qt Multimedia ne peut pas la lire.

### Dépendances ou démarrage

Relancez `start.bat`, ou installez les paquets avec :

```powershell
python -m pip install --user -r requirements.txt
```

## Aide et contact

Pour une question ou un problème, contactez **`lupinducoup` sur Discord**.
N'envoyez jamais votre `.env`, mot de passe, jeton ou capture d'écran contenant
des identifiants.

---

<div align="center">

**LUPIN TOOL — rester dans l'ombre, garder les accès privés.**

</div>
