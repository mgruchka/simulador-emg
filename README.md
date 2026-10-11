# simulador-emg

O trabalho que originou esse projeto tinha como objetivo realizar uma simulação in silico do funcionamento um aparelho de EMG descrito em "Long-term recording of electromyographic activity from multiple muscles to monitor physical activity of participants with or without a neurological disorder" (Gant et al.; 2017). 

A simulação funciona em três etapas: 1) geração de um sinal que simula a tensão captada por dois eletrodos de área durante uma única contração de um músculo sob a pele (parametrizado por tempo e força da contração). 2) input do sinal gerado (salvo em .txt) no esquemático do LTSpice, simulação do fluxo de sinal no dispositivo e exportação do sinal digital convertido pelo ADC (em .txt). 3) conversão do .txt de saída do LTSpice em .dat para leitura no Open Ephys GUI, onde o arquivo pode ser carregado e visualizado num ambiente desenvolvido para o monitoramento de sinais de EMG (permitindo validação e comparação das simulações). 

Esse repositório contém:

- 1 script .py com duas funções principais: a geração do sinal e exportação em .txt para input no LTSpice; conversão do .txt gerado na saída no LTSpice em .dat para leitura no Open Ephys GUI. 
- 1 esquemático .asc (LTSpice) executável para simulação do circuito do dispositivo descrito.  
- Arquivos de exportação para cada etapa e resultados de 4 testes realizados (.txt, .dat, .png). 
- 1 .pdf do trabalho que motivou esse repositório se quiser ler mais a respeito e conferir a bibliografia :). 

Note: os dados gerados pelo simulador são apenas aproximações que pude desenvolver com as ferramentas do NumPy e do SciPy a partir dos modelos fisiológicos validados sobre a variação de potencial no tecido muscular em atividade. Os resultados desse trabalho, além de satisfazer minha curiosidade, pode ser úteis para a simulação de circuitos de ADC (analog-to-digital converter) e leitura de EMG no Open Ephys GUI, mas provavelmente não servem para uma modelagem rigorosa da eletrofisiologia do tecido muscular. 
