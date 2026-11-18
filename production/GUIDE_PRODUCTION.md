# LE 71 Flash News — Guide de production

Bible de la rédaction et de la production. Toute session (manuelle ou programmée) qui fabrique un flash suit ce guide.

## 1. Identité

- **Média** : LE 71 Flash News — actualité locale de la Saône-et-Loire, vidéos verticales 9:16 pour TikTok (@flashnews71000).
- **Présentatrice** : **Léa**, journaliste en Saône-et-Loire. Voix douce, posée, professionnelle, bien articulée. Sympathique et proche, jamais familière. Elle vouvoie (« vous »).
- **Charte (depuis le 17 nov. 2026) : mise en page « sombre »**, mélange des deux premières présentations. Fond sombre sur toute la vidéo (les boutons TikTok — j'aime, commentaires, partages — restent lisibles) ; transitions « breaking news » (volet rouge en biais avec le logo LE 71) entre chaque partie ; carte du 71 en 3D, grande, sur chaque sujet (repère sur la commune ~3 s, puis l'illustration) et au sommaire ; titres en blanc, rouge réservé aux bandeaux et mots forts ; aucun texte dans la colonne de droite (x > 920, y 850→1560) ni sous y 1565 (légende TikTok) ; météo, écran de fin et couverture en sombre. Titres Barlow Condensed italique, textes Inter. Le générique « LE 71 · FLASH NEWS · SAÔNE-ET-LOIRE » ouvre TOUJOURS la vidéo, identique d'une vidéo à l'autre. L'ancienne charte rouge sur fond blanc n'est plus utilisée.
- **Météo du jour dans le Réveil 71** (à inclure chaque matin, depuis le 18 nov. 2026) : ajouter à l'épisode `"meteo": {"titre1": "LA MÉTÉO", "titre2": "DU JOUR", "periode": "…", "source": "…", "villes": [...]}` et `voix.meteo` ; la page s'insère après le sommaire. `sommaire_items` (liste de {tag, short}) permet d'afficher la météo dans le sommaire. **Villes demandées par l'éditeur, toujours ces 6, dans cet ordre** : `{"nom": "Digoin"}`, `{"nom": "Paray-le-Monial", "label": "Paray"}`, `{"nom": "Montceau-les-Mines", "label": "Montceau"}`, `{"nom": "Autun"}`, `{"nom": "Chalon-sur-Saône", "label": "Chalon"}`, `{"nom": "Mâcon"}` — chacune avec `ciel` et `tmax` du jour, valeurs relevées ville par ville (aucune valeur estimée ou recopiée d'une ville voisine). Le moteur écarte automatiquement les étiquettes trop proches (Digoin/Paray, Autun/Montceau) avec un trait de rappel ; un réglage manuel reste possible avec `"decal": [dx, dy]`. `voix.meteo` : 2 ou 3 phrases courtes — le temps général, puis les 6 températures regroupées (« 12 degrés à Digoin et Paray, 11 à Montceau et Autun, 13 à Chalon et Mâcon »), puis un conseil pratique si besoin (pluie, gel, vent).
- Canevas de la charte : https://claude.ai/artifact/PNPySHBQ7XZv1Wv7jSh9a8

## 2. Les rendez-vous

| Rendez-vous | Format moteur | Publication | Préparation | Contenu |
|---|---|---|---|---|
| **Le Réveil 71** (lun–sam) | `matin` | 8h00 (depuis le 19 nov. 2026) | ~6h45 | Ce qui se passe AUJOURD'HUI (événements, travaux, circulation, grèves, marchés) + 1 fait marquant de la veille/nuit |
| **Le 20h du 71** (lun–sam) | `soir` | 20h00 | ~18h45 | Bilan : les 2 ou 3 infos importantes de la journée dans le 71 |
| **La météo de la semaine** (dimanche) | `meteo` | 18h30 | ~17h15 | Prévisions lundi→dimanche, carte des villes |

Le dimanche, la météo remplace le 20h. Pas de Réveil 71 le dimanche.

## 2 bis. Ce qui fonctionne — À REPRODUIRE (mis à jour à partir des statistiques)

Bilan des 9 premières vidéos (15–16 nov. 2026, 509 abonnés) : ~25 400 vues, 419 j'aime, 64 partages, 2 commentaires.

1. **L'alerte info locale est notre meilleur format.** « Accident sur la RCEA à Molinet » (28 s) : 17 065 vues, 217 j'aime, 49 partages — 2/3 de l'audience totale. Ce qui a marché : info chaude (moins de 12 h), qui touche le quotidien (la route), lieu précis, bilan factuel, conseil de prudence, très court. → Format **ALERTE 71** (section 5 bis) dès qu'un événement important le justifie.
2. **Les vidéos de 25 à 40 s performent le mieux.** Les formats « flash ville » (Paray & Charolles, 36 s, 1 695 vues), « présentation du compte » (31 s, 1 528) et « témoignage » (Cluny, 38 s, 1 394) tiennent bien. → Flashes matin/soir : **viser 45 à 60 s**, 2 sujets forts plutôt que 3 moyens. Alerte : **20 à 35 s**.
3. **Le local concret et utile** (routes, sécurité, météo qui impacte, sorties près de chez soi) l'emporte sur l'institutionnel (budget du Département : 203 vues). → Toujours chercher l'angle « ce que ça change pour vous », le dire dès la première phrase du sujet.
5. **Règle des 10 secondes** (mesure Windsor, 9 vidéos) : nos spectateurs regardent en moyenne **~10 s**, quelle que soit la durée de la vidéo (73 s → 12 s ; 28 s → 10 s). Les vidéos qui attaquent directement sur l'info gardent le mieux (RCEA 37 % de la vidéo vue, 7 % de visionnages complets, 354 abonnés gagnés) ; les vidéos « présentation / appel au partage » décrochent en 4 à 6 s. → **L'info la plus forte est dite et affichée dans les 3 premières secondes** : générique raccourci à 1,5 s, puis l'ACCROCHE (champ `accroche`) avant même la présentation de Léa ; le sujet le plus fort est le sujet n°1.
4. **Le partage vient de l'utilité** (prévenir ses proches). → Finir les sujets utiles par « Partagez à ceux qui prennent cette route / qui habitent à… ».

## 2 ter. À corriger

1. **Presque aucun commentaire** (2 sur 9 vidéos). → Chaque vidéo se termine par UNE question simple et locale, affichée à l'écran (champ `question` de l'épisode) et dite par Léa, et reprise en tête du descriptif ; donner la phrase à épingler en commentaire dans le compte rendu.
2. **Trop de vidéos à la suite** (7 en 2 h le samedi soir) : elles se concurrencent. → Respecter les rendez-vous ; une ALERTE ne part jamais à moins de 90 min d'une autre vidéo LE 71 (sauf danger immédiat).
3. Sujets institutionnels sans angle concret : à éviter ou à reformuler.

## 2 quater. Rituel statistiques (chaque séance)

Avant d'écrire : relever dans Metricool (marque LE 71, réseau tiktok, connecteur posts : TKPO02 date, TKPO05 description, TKPO06 durée, TKPO07 vues, TKPO08 j'aime, TKPO09 commentaires, TKPO10 partages ; évolution : TKEV07 abonnés) les vidéos des 7 derniers jours. Ajouter une ligne datée dans STATS.md du dépôt (abonnés, meilleure vidéo, vues/partages des dernières vidéos). Le lundi soir : analyse de la semaine et mise à jour des sections 2 bis et 2 ter de ce guide dans le dépôt (fichier LECONS.md), en comparant formats, durées, thèmes et horaires. **Reproduire ce qui marche** (thème, durée, accroche, type de question) avant de corriger le reste.

## 3. Règles éditoriales (non négociables)

1. **2 sujets, 3 maximum** par flash, annoncés dans un sommaire au début.
2. **Accroche immédiate** : la première phrase après le bonjour dit pourquoi rester.
3. **Vérifier la DATE de chaque info.** Les moteurs de recherche mélangent les années (ex. un article de nov. 2025 ressort en nov. 2026). Une info n'entre dans le flash que si sa date est confirmée par la source (date de publication ou date de l'événement explicite, année comprise).
4. **Recouper** : idéalement deux sources, ou une source officielle (préfecture, mairie, Département, DREAL, organisateur, club). Sources préférées : Le JSL (lejsl.com), France 3 Bourgogne-Franche-Comté, macommune.info, Lyon Capitale (rubrique 71), La Gazette France, sites des villes, préfecture de Saône-et-Loire, Météo-France.
5. **Ne rien inventer** : pas de chiffre, de nom ou de citation non sourcé. Une info douteuse est écartée.
6. **Prudence** : faits divers sans nommer de personnes privées, présomption d'innocence (« mis en examen », « soupçonné »), pas de détails choquants, pas de contenu sur des mineurs identifiables.
7. **Neutralité** politique : faits, pas d'opinion.
8. Jour calme : un flash court avec 1 ou 2 vraies infos vaut mieux qu'un remplissage.
9. Chaque sujet indique sa **source** à l'écran (champ `source`).

## 4. Écriture de la voix de Léa

- Phrases courtes, une idée par phrase. Virgules = respiration, points = pauses.
- Écrire les heures en toutes lettres pour la synthèse : « 20 heures 30 », « 18 heures ». À l'oral, le flash du soir s'appelle TOUJOURS « le 20 heures du 71 » (jamais « 20h », qui est seulement l'écriture à l'écran). Le moteur convertit aussi automatiquement « 20h » en « 20 heures » dans la voix, par sécurité.
- Annoncer le lieu dans chaque sujet.
- Durée cible : 45 à 60 s (matin/soir), 50 à 70 s (météo), 20 à 35 s (alerte).
- **Format « explicatif »** (présentation du département, d'une ville, d'un dossier — format `special`) : plus pédagogique. Chaque sujet explique en 3 ou 4 phrases : le fait, le chiffre, puis le *pourquoi* ou le contexte (« notre département tient son nom de deux rivières… », « c'est là qu'est né Nicéphore Niépce… »). Durée cible **80 s à 1 min 40**. La règle des 10 secondes s'applique quand même : accroche chiffrée d'abord.
- **Sigles épelés lettre par lettre** : R C E A, T G V, S N C F, T E R, S D I S, C H U, E D F, R N. Le moteur le fait automatiquement (la synthèse lisait « RCEA » comme un mot anglais) ; pour un nouveau sigle, l'écrire avec des espaces dans la voix (« S N C F »). Les autoroutes : « l'A6 » est lu « A 6 ».
- Rythme : transitions courtes (le moteur enchaîne les scènes sans temps mort). Phrases de sujet de 1 à 2 lignes ; pour un agenda (ex. 5 sorties), une phrase par sortie : jour, heure, quoi, où.
- Première phrase de chaque sujet = ce que ça change pour le spectateur.
- Finir par la question du champ `question` (« Et vous, … ? »), puis l'appel à s'abonner.
- **Ouverture = accroche d'abord** : `voix.intro` = l'accroche du jour en UNE phrase factuelle (l'info la plus forte), PUIS la présentation. Ex. : « Grave accident sur la RCEA cette nuit. Salut, je suis Léa, voici le 20 heures du 71. » Le champ `accroche` (4 à 8 mots, affiché en grand dès 1,5 s sous « À LA UNE ») reprend cette info. Jamais d'accroche trompeuse ou sensationnaliste.
- Présentations types (après l'accroche) :
  - Matin : « Salut, je suis Léa, voici le Réveil 71. »
  - Soir : « Salut, je suis Léa, voici le 20 heures du 71. »
  - Météo : « Salut, je suis Léa, voici la météo de la semaine en Saône-et-Loire. »
- **Sommaire (champ `voix.sommaire`) : UNE phrase synthétique, sans détail.** « Au sommaire ce soir : [sujet 1], [sujet 2] et [sujet 3]. » (« ce matin » pour le Réveil 71). Chaque sujet en 3 à 5 mots, sans chiffre, sans explication, sans heure : les détails viennent dans chaque sujet. Exemple : « Au sommaire ce soir : David Hallyday à Mâcon, le Marché des Plaisirs Gourmands et l'Élan Chalon face à Saint-Quentin. »
- Transitions : « On file maintenant à [ville]… », « Autre info, direction [ville]… »
- Fin : « C'était [le Réveil 71 / le 20 heures du 71]. Abonnez-vous, partagez autour de vous… et [rendez-vous ce soir à 20 heures / à demain matin] ! »

## 5. Le moteur vidéo

Fichiers (Dropbox `/LE 71/production/`) : `le71.py`, `d71.json` (contour exact du 71), `setup.sh`, ce guide.

```
bash setup.sh
python3 le71.py episode.json sortie.mp4 --stills apercus/
```

Le moteur génère la voix de Léa avec **OmniVoice** (le moteur de VoiceStudio), clonée à partir de `voice/lea_ref.wav` (voix créée par l'éditeur dans VoiceStudio, le 18 nov. 2026 ; texte lu dans `voice/lea_ref.txt`). Si OmniVoice est absent ou plante, le moteur bascule automatiquement sur Piper (voix siwis) et l'écrit dans la console (« ATTENTION : voix de Léa… ») : le signaler dans le compte rendu. `LE71_TTS=piper` force l'ancienne voix. Réglages facultatifs de l'épisode : `lea_speed` (0.85 par défaut, plus grand = plus rapide), `lea_steps` (20, qualité), `prononciation` ({"Nom": "lecture"} si un nom est mal dit ; dictionnaire général `PRONONCIATION` dans le71.py). Le moteur lit « 71 » « soixante et onze » et détache les noms composés (Paray le Monial). **Temps de calcul** : sur le serveur (processeur seul), compter ~12 min pour une alerte de 30 s et ~25 min pour un flash de 60 s, soit plus que la limite d'une commande : **lancer le rendu en arrière-plan** dès le début de la préparation et attendre la ligne « OK … s ». Le moteur anime chaque scène, cale l'image sur la voix et produit un MP4 1080×1920, 30 i/s. Les communes sont placées automatiquement à leur position exacte (geo.api.gouv.fr).

### Fichier épisode — formats `matin`, `soir`, `special`

```json
{
 "format": "soir",
 "date_label": "Mar. 17 nov.",
 "voice_speed": 1.05,
 "accroche": "Grave accident sur la RCEA cette nuit",
 "question": "Vous prenez souvent la RCEA ?",
 "ticker": "Le 20h du 71  •  L'essentiel de la journée en Saône-et-Loire  •  Abonnez-vous à LE 71 Flash News  •",
 "voix": {
  "intro": "Grave accident sur la RCEA cette nuit. Salut, je suis Léa, voici le 20 heures du 71.",
  "sommaire": "Au sommaire ce soir : [sujet 1], [sujet 2] et [sujet 3].",
  "fin": "C'était le 20 heures du 71. Abonnez-vous, partagez autour de vous… et rendez-vous demain matin !"
 },
 "items": [
  {"tag": "CHALON", "band": "MAR. 17 NOV.", "short": "Titre court pour le sommaire",
   "title": "Titre accrocheur (6-9 mots)", "desc": "L'essentiel en une phrase.",
   "place": "Lieu précis, Commune", "commune": "Chalon-sur-Saône", "theme": "economie",
   "source": "Le JSL", "voix": "Texte lu par Léa pour ce sujet."}
 ]
}
```

- `tag` : mot court dans la case rouge du sommaire (AUJ., HIER, ROUTE, nom de ville, DEMAIN…).
- `band` : bandeau noir sous l'image (date/heure).
- `theme` (illustration animée, aussi utilisée sur la couverture) — **choisir celui qui correspond vraiment au sujet n°1**, sinon `generic` : `route` (travaux, circulation), `secours` (faits divers, pompiers, accidents), `batiment` (artisans, chantiers, logement), `economie` (industrie, entreprises, emploi), `mairie` (politique locale, conseil municipal), `justice` (tribunal, procès, condamnation), `sante` (hôpital, urgences, médecins), `ecole` (écoles, collèges, lycées), `campagne` (agriculture, ruralité), `course` (course à pied, corrida, trail : coureurs en ville et arche d arrivée), `football`, `basket`/`sport`, `marche`, `concert`, `humour`, `theatre`/`culture`, `generic`. Jamais une illustration qui contredit le sujet (ex. `economie`, avec sa courbe qui monte, pour une mauvaise nouvelle économique : préférer `batiment`, `mairie` ou `generic`).

- `question` (au niveau de l'épisode, recommandé) : la question finale affichée sur l'écran de fin, ex. « Vous prenez souvent la RCEA ? ».

### Fichier épisode — format `alerte` (ALERTE 71)

Même structure que `soir`, avec 1 seul sujet (2 au maximum), `voix` = {"intro": "Alerte info en Saône-et-Loire.", "fin": "…"} (pas de `sommaire`). Ouverture choc rouge « ALERTE 71 » avec le titre court du sujet. `commune` doit être une commune de Saône-et-Loire (la plus proche si l'événement est à la limite du département). Thèmes usuels : `secours`, `route`.

### Fichier épisode — format `meteo`

```json
{
 "format": "meteo", "date_label": "Dim. 22 nov.",
 "voix": {"intro": "…", "carte": "Vue d'ensemble par ville…", "semaine": "Le détail jour par jour…", "fin": "Bonne semaine à tous !"},
 "meteo": {
  "periode": "Du 23 au 29 novembre",
  "villes": [
   {"nom": "Autun", "ciel": "nuages", "tmax": 7},
   {"nom": "Chalon-sur-Saône", "label": "Chalon", "ciel": "eclaircies", "tmax": 9},
   {"nom": "Montceau-les-Mines", "label": "Montceau", "ciel": "pluie", "tmax": 8},
   {"nom": "Louhans", "ciel": "nuages", "tmax": 9},
   {"nom": "Paray-le-Monial", "label": "Paray", "ciel": "pluie", "tmax": 8},
   {"nom": "Mâcon", "ciel": "soleil", "tmax": 10}
  ],
  "jours": [{"jour": "Lundi", "ciel": "soleil", "tmax": 10, "tmin": 2}]
 }
}
```

- `ciel` : `soleil`, `eclaircies`, `nuages`, `pluie`, `orage`, `neige`.
- Garder ces 6 villes (lisibles sur la carte). Valeurs `tmax` des villes = pour le lundi ou moyenne de la semaine (le dire dans la voix).
- 7 jours, lundi → dimanche. Source : Météo-France (ou prévisions publiées citant Météo-France).

## 5 bis. ALERTE 71 — quand la déclencher

Uniquement pour un événement **important, récent (moins de 6 h), vérifié par au moins une source fiable datée**, qui concerne directement les habitants du 71 : accident grave ou fermeture d'un grand axe (RCEA/N79/N70, A6, A39, N80…), incendie important, intempéries avec vigilance orange/rouge Météo-France, coupure majeure (eau, électricité, transports), alerte des autorités (préfecture, gendarmerie). Jamais : rumeur, info non confirmée, détail sordide, nom de victime ou de suspect. En cas de doute : pas d'alerte, le sujet peut entrer dans le prochain flash.

## 6. Contrôle qualité avant publication

1. Rendre avec `--stills` et REGARDER chaque aperçu : textes qui débordent, titres trop longs (> 3 lignes), étiquettes de carte qui se chevauchent, commune mal placée.
2. Vérifier la durée (sortie « OK … s »).
3. Relire la voix : noms propres, chiffres, dates.
4. Corriger et relancer si besoin. Une seule vidéo publiée, jamais une version douteuse.

## 6 bis. Couverture (1re image de la vidéo)

Le moteur place automatiquement une **couverture fixe de 0,3 s en tout début de vidéo** (TikTok prend la 1re image comme couverture). Elle est conçue pour la **grille du profil**, où TikTok recadre en 3:4 (seule la bande y 240 → 1680 est visible) et pose le **compteur de vues en blanc, en bas à gauche**.

- **Le titre est l'élément le plus gros** : c'est lui qui fait cliquer. De haut en bas : bandeau rouge du rendez-vous (discret), visuel (photo de terrain ou illustration du thème du sujet n°1), **titre = l'info principale** (2 lignes de préférence, 3 au maximum ; viser 4 à 8 mots), puis **bande sombre** : à gauche RIEN (zone du compteur de vues), à droite la commune et la date.
- **Photo de terrain** : dès qu'on en a une (photo de l'éditeur ou libre de droits, jamais une photo de presse), elle remplace l'illustration et rend la couverture bien plus forte. Champ `"photo"` du sujet ou de `couverture`.
- Ne jamais mettre de texte ni de fond clair dans le coin bas-gauche de la bande visible (x < 440, y 1500 → 1680) : le compteur deviendrait illisible.
- Réglages facultatifs dans l'épisode : `"couverture": {"titre": "…", "lieu": "…", "photo": "chemin.png", "instant": 4.0, "cadrage": 150}` (`instant` = moment de l'animation figé sur la couverture, `cadrage` = hauteur de ciel masquée) ; `"couverture": false` pour la retirer. Par défaut : titre = `accroche` (ou `title` du 1er sujet pour une alerte), lieu = `commune` du 1er sujet.
- Export seul : `python3 le71.py episode.json - --cover couverture.png`. À contrôler avec les aperçus (`--stills` produit `couverture.png`) : titre lisible et non coupé, illustration cohérente avec le sujet, rien qui touche les bords.

## 7. Publication

1. Hébergement : déposer la vidéo dans le dépôt GitHub public `bekimdocs-gif/le71-videos` (`videos/AAAA-MM/`), vérifier le lien `https://raw.githubusercontent.com/bekimdocs-gif/le71-videos/main/videos/...` (HTTP 200), puis programmer dans Metricool (marque « Le 71 », blogId 8028968, réseau tiktok) à l'heure du rendez-vous, avec `isAigc: true`, `privacyOption: PUBLIC_TO_EVERYONE`, `autoAddMusic: false`, un `title` TikTok court.
2. Validation : la vidéo est programmée ~1h avant ; envoyer à l'éditeur (Bekim) une notification avec l'aperçu, le texte et le lien du planning Metricool pour qu'il puisse annuler ou corriger.
3. Si le Mac n'est pas joignable : envoyer la vidéo et le descriptif prêts à poster (fichier + notification), à publier depuis l'application TikTok ou Metricool.

### Descriptif TikTok (modèle)

```
[Emoji] [Accroche du flash en une ligne]

📍 [Commune] – [info 1 en une ligne]
📍 [Commune] – [info 2 en une ligne]

[La question finale, la même qu'à l'écran] 👇
🔔 Abonnez-vous à LE 71 Flash News pour ne rien manquer de l'actu du 71 !

#SaôneEtLoire #71 #[Ville1] #[Ville2] #FlashNews71 #ActuLocale
```
