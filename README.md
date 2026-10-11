# simulador-emg

O trabalho que originou esse projeto tinha como objetivo realizar uma simulação in silico de um aparelho de EMG descrito no artigo de Gant et al. (2017). 

Esse repositório contém:

- 1 script .py de gravação bipolar com eletrodos de área para EMG. 
- 1 esquemático .asc (LTSpice) executável para simulação in silico de um dispositivo de eletromiografia portátil. 
- Arquivos e resultados de 4 testes realizados (.txt, .dat, .png). 
- 1 .pdf do trabalho que motivou esse repositório se quiser ler mais a respeito e conferir a bibliografia :). 

Importante: os dados gerados pelo simulador são aproximações que pude desenvolver com as ferramentas do NumPy e do SciPy a partir dos modelos fisiológicos validados sobre a variação de potencial no tecido muscular em atividade. Os resultados desse trabalho, além do valor de aprendizado, são mais úteis para a simulação de circuitos de ADC (analog-to-digital converter) e leitura de EMG do que para a modelagem rigorosa dos fenômenos eletrofisiológicos. 