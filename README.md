# Model trainen:

vanuit de parent directory: 
```powershell
python train_model.py model_architectures/[path naar model] [stanford_frames/HMDB_frames/OF] [aantal epochs] [optioneel: path naar model weights]
``` 

Hij traint en print per epoch de loss en accuracy voor test en validation. Hij houdt bij wat het beste model is en slaat die uiteindelijk op. Als je op ctrl + c drukt tijdens trainen, stop je de loop, maar hij zou het beste model moeten opslaan (werkt niet altijd fantastisch, met name als je vaker dan ééns snel achter elkaar op ctrl + c drukt.)

in het train_model.py aan te passen: learning rate in de optimizer
als je in train() cyclical_learning_rate naar true zet doet ie een cyclical learning rate. De parameters daarvan kun je in de train functie aanpassen. 