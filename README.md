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
3. Configurez Scraphub en suivant la section ci-dessous.
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

Le fichier modèle se trouve dans `settings/options/.env.example`. Pour le
configurer :

1. Dans l'explorateur de fichiers, ouvrez `settings/options`.
2. Copiez `.env.example` dans le même dossier.
3. Renommez la copie en `.env` (le nom final doit être exactement `.env`, sans
   extension supplémentaire comme `.txt`).
4. Ouvrez `.env` avec un éditeur de texte et renseignez les valeurs fournies
   pour **votre propre accès Scraphub** :

```dotenv
SCRAPHUB_API_URL=
SCRAPHUB_EMAIL=
SCRAPHUB_PASSWORD=
```

- `SCRAPHUB_API_URL` : l'adresse API communiquée par l'administrateur du service
  Scraphub auquel vous avez accès. Ne devinez pas cette adresse. Si vous ne la
  connaissez pas, demandez-la à l'administrateur de votre service.
- `SCRAPHUB_EMAIL` : l'adresse e-mail de votre compte Scraphub.
- `SCRAPHUB_PASSWORD` : le mot de passe de votre compte Scraphub.

Enregistrez le fichier, puis relancez l'application. La recherche lit ce fichier
localement au démarrage. L'adresse API doit utiliser HTTPS.

### Garder les identifiants privés

Le `.env` contient des identifiants en texte lisible sur votre ordinateur :

- Ne le publiez pas, ne le joignez pas à un ZIP et ne l'envoyez pas sur Discord.
- Le `.env` est ignoré par Git; seul `.env.example`, qui ne contient pas vos
  valeurs, est destiné au dépôt.
- Chaque personne doit utiliser son propre compte et créer son propre `.env`.
- Si vous avez déjà partagé un mot de passe ou commité un vrai `.env`, changez
  immédiatement ce mot de passe auprès du service.

**Important pour les développeurs :** cacher `SCRAPHUB_API_URL` dans le code ou
la mettre dans `.env` ne la rend pas secrète dans une application distribuée.
L'URL utilisée par un client peut être retrouvée en inspectant ses fichiers ou
ses connexions réseau. Une URL d'API n'est généralement pas un secret
d'authentification; les mots de passe, jetons et clés privées, eux, le sont.
L'obfuscation ne protège pas ces secrets.

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

### « URL API absente »

Vérifiez que le fichier s'appelle exactement `.env`, qu'il est dans
`settings/options`, et que `SCRAPHUB_API_URL` a été renseignée.

### « Identifiants absents »

Vérifiez que `SCRAPHUB_EMAIL` et `SCRAPHUB_PASSWORD` sont remplis dans le `.env`
local. Ne collez pas vos identifiants dans un message public pour demander de
l'aide.

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
