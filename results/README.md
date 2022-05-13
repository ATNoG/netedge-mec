#Attention!!
The parser requires manually deleting directories that don't have the proper fields which means something went wrong with the deployment (i.e docker blocked our image pulls)
The parser is also obtaining all the time for the main_ns even if some aren't the proper ones. Fix this manually by removing the initial times and the respective csv fields
