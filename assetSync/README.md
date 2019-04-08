assetSync is the small set of python scripts I put together for a Google Drive -> github -> CDN pipe for a mobile game.

syncArtExportsToUnity.py synced spine export files and sprite assets to the appropriate directory structure for the CDN bundle process
syncUIArtAssetsToUnity.py did pretty much the exact same thing but to a different unity project and it was run by differnent users
manifestToXlsx.py was used to update the design xlsx sheets with the name(s) of content uploaded to the CDN
removeGoogleIcon.py removed a silly bunch of '?' hidden characters that Google Drive would create and mess up the rest of the process.
