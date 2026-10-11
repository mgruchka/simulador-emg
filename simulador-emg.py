import numpy as np
import matplotlib.pyplot as plt
import json
import os
import shutil



# 0. DEFINIÇÃO DE PARÂMETROS 

FS = 10_000                  # valor discreto para simular leitura contínua do eletrodo (Hz)
FS_ADC = 1_000               # frequência de amostragem ADC simulado (Hz)
DIAMETRO_ELETRODO_MM = 10.0  
DISTANCIA_ELETRODOS_MM = 20.0  # centro a centro
VELOCIDADE_MM_S = 4_000.0     
RUIDO_UV = 4.4                # aproximação do ruído medido em Gant et al., 2017
SEMENTE = 42                  # seed para testagem repetível
rng = np.random.default_rng(SEMENTE)



# 1. DEFINIÇÃO DE FUNÇÕES

def muap_gen(fs, st, depth_mm, amp_uv, lambda_val=1.0):
    '''Retorna duas matrizez com valores de tensão (mV) numa unidada motora, uma para cada eletrodo.'''

    # Perfil com forma relacionada à segunda derivada de Rosenfalck
    duracao_muap_s = 0.020
    n = round(duracao_muap_s * fs)
    z = np.linspace(0, 10, n)
    x = lambda_val * z
    onda = (6*x - 6*x**2 + x**3) * np.exp(-x)
    onda = onda - np.mean(onda)  # aproxima sinal bipolar em torno de zero

    pico = np.max(np.abs(onda))
    if pico > 0:
        onda = onda / pico * amp_uv

    # Profundidade: atenuação e suavização qualitativas
    # Valores escolhidos apenas para obter uma tendência plausível
    atenuacao = 1.0 / (1.0 + depth_mm / 5.0)
    sigma_ms = 0.15 + 0.06 * depth_mm
    sigma_amostras = max(1, round(sigma_ms * fs / 1000))
    k = np.arange(-3*sigma_amostras, 3*sigma_amostras + 1)
    h_tecido = np.exp(-0.5 * (k / sigma_amostras)**2)
    h_tecido = h_tecido / np.sum(h_tecido)
    onda = np.convolve(onda, h_tecido, mode='same') * atenuacao

    # Eletrodo de área: média temporal equivalente ao diâmetro / velocidade.
    tempo_eletrodo_s = (DIAMETRO_ELETRODO_MM / VELOCIDADE_MM_S)
    n_eletrodo = max(1, round(tempo_eletrodo_s * fs))
    h_eletrodo = np.ones(n_eletrodo) / n_eletrodo
    muap_eletro1 = np.convolve(onda, h_eletrodo, mode='same')

    # Propagação por 20 mm entre os centros dos eletrodos.
    atraso_s = DISTANCIA_ELETRODOS_MM / VELOCIDADE_MM_S
    atraso_amostras = round(atraso_s * fs)
    muap_eletro2 = np.zeros_like(muap_eletro1)
    if atraso_amostras < len(muap_eletro1):
        muap_eletro2[atraso_amostras:] = muap_eletro1[:-atraso_amostras]

    return muap_eletro1, muap_eletro2


def muap_sum(eletro1_raw, eletro2_raw, n_mu, fs, st, f_disp_range):
    '''Soma n_mu unidades motoras em eletro1_raw e eletro2_raw, com ruído adicionado, 
    com n_mu determinado pela nível de contração escolhido pelo usuário em emg_simulator().'''

    for i in range(n_mu):
        depth_mm = rng.uniform(2.0, 15.0)
        lambda_mu = rng.uniform(0.7, 1.2)
        amp_mu = rng.uniform(6.8, 25.5)  # escala nominal herdada do original, em uV

        muap_e1, muap_e2 = muap_gen(fs, st, depth_mm, amp_mu, lambda_mu)
        f_disp = rng.uniform(*f_disp_range)
        intervalo_medio = 1.0 / f_disp
        t_atual = rng.uniform(0, intervalo_medio)

        while t_atual < st:
            centro = round(t_atual * fs)
            inicio = centro - len(muap_e1) // 2
            fim = inicio + len(muap_e1)

            # Recorte dos índices nos limites da gravação.
            a = max(0, inicio)
            b = min(len(eletro1_raw), fim)
            if a < b:
                eletro1_raw[a:b] += muap_e1[a-inicio:b-inicio]
                eletro2_raw[a:b] += muap_e2[a-inicio:b-inicio]

            # Variação de 15% nos intervalos, sem valores não-físicos negativos.
            proximo = rng.normal(intervalo_medio, 0.15 * intervalo_medio)
            while proximo <= 0.002:
                proximo = rng.normal(intervalo_medio, 0.15 * intervalo_medio)
            t_atual += proximo

    ruido_e1 = rng.normal(0, RUIDO_UV, len(eletro1_raw))
    ruido_e2 = rng.normal(0, RUIDO_UV, len(eletro2_raw))
    return eletro1_raw + ruido_e1, eletro2_raw + ruido_e2


def txt_export(sim_name, matrix1, matrix2, timelength):
    '''exporta as matrizes geradas em txt para o LTspice, com duas colunas: tempo (s) e tensão (V).'''

    arquivo_e1 = f'{sim_name}_e1.txt'
    arquivo_e2 = f'{sim_name}_e2.txt'
    for arquivo, sinal in [(arquivo_e1, matrix1), (arquivo_e2, matrix2)]:
        with open(arquivo, 'w', encoding='utf-8') as f:
            for tempo, valor_uv in zip(timelength, sinal):
                f.write(f'{tempo:.7f}\t{valor_uv * 1e-6:.12f}\n')
    cwd = os.getcwd()

    print(f"Arquivos exportados em: {os.path.join(cwd, f"{sim_name}_e1.txt")} e {os.path.join(cwd, f"{sim_name}_e2.txt")}.")
    print("Informe o tempo de medição em '.tran 0 **TEMPO** 0 10u' no LTSpice antes de rodar sua simulação.")


def emg_simulator(st=None, n_mu=None, strength=None, sim_name=None, mostrar=True):
    '''UI simples para obter os parâmetros da simulação.'''

    if st is None:
        st = float(input('Tempo de medição, em segundos: '))
    if n_mu is None:
        n_mu = 80  # max unidades motoras
    if strength is None:
        strength = int(input('Nível de força muscular (0 a 4): '))
    if sim_name is None:
        sim_name = input('Nome base para essa simulação: ').strip()

    if st <= 0 or n_mu < 0 or strength not in range(5) or not sim_name:
        raise ValueError('Confira: tempo > 0; unidades >= 0; força 0–4; nome não vazio.')

    frequencias = {0: None, 1: (10, 15), 2: (15, 20),
                    3: (20, 25), 4: (25, 30)}
    total = round(st * FS)
    tempo = np.arange(total) / FS
    e1 = np.zeros(total)
    e2 = np.zeros(total)

    proporcoes = {0: 0.0, 1: 0.10, 2: 0.30, 3: 0.60, 4: 1.0}
    unidades_ativas = round(n_mu * proporcoes[strength]) # soma de muaps determinada pela força da contração 
    faixa = frequencias[strength] if strength > 0 else (10, 15)
    e1, e2 = muap_sum(e1, e2, unidades_ativas, FS, st, faixa)
    bipolar = e1 - e2  # visualização; entradas individuais são exportadas
    txt_export(sim_name, e1, e2, tempo)


def txt2dat_emg(ltsp_file=None, inicio_s=0.5, nome_saida='Simulacao_OpenEphys'):
    '''Converte o TXT exportado do LTSpice em .dat para leitura no Open Ephys.

    inicio_s determina um tempo de corte em relação ao começo da medição 
    registrada no .txt; aqui padronizado em 0.5s.
    
    A maior parte da função são só pequenos ajustes para compatiblidade
    com o formato de dados que Open Ephys GUI espera.'''

    if ltsp_file is None:
        ltsp_file = input('Nome do TXT exportado do LTspice: ').strip()

    # Tratamento de cabeçalho
    with open(ltsp_file, 'r', encoding='utf-8-sig') as f:
        primeira_linha = f.readline().strip().replace(',', '.')
    try:
        float(primeira_linha.split()[0])
        pular_cabecalho = 0
    except (ValueError, IndexError):
        pular_cabecalho = 1
    dados = np.loadtxt(ltsp_file, skiprows=pular_cabecalho)
    dados = np.atleast_2d(dados)
    if dados.shape[1] < 2:
        raise ValueError('O TXT deve conter pelo menos duas colunas: tempo e tensão.')
    t, v = dados[:, 0], dados[:, 1]

    # Ordena o tempo e elimina eventuais valores repetidos
    ordem = np.argsort(t)
    t, v = t[ordem], v[ordem]
    t, indices = np.unique(t, return_index=True)
    v = v[indices]
    mascara = t >= inicio_s
    t, v = t[mascara], v[mascara]
    if len(t) < 2:
        raise ValueError('Poucos dados após o corte inicial: diminua inicio_s.')

    # Um ponto no meio de cada periodo de 1 ms, longe das bordas do clock
    # No esquema, o pulso do sample/hold dura 100 us em cada periodo
    # Assim evitamos quantizar o sinal novamente
    primeiro_indice = int(np.ceil((t[0] - 0.0005 - 1e-10) * FS_ADC))
    ultimo_indice = int(np.floor((t[-1] - 0.0005 + 1e-10) * FS_ADC))
    t_adc = (np.arange(max(0, primeiro_indice), ultimo_indice + 1) + 0.5) / FS_ADC
    if len(t_adc) == 0:
        raise ValueError('O arquivo nao contem um patamar completo do clock de 1 kHz.')
    v_adc = np.interp(t_adc, t, v)
    print('Convertendo V(LOGGER-CF), ja digitalizado no LTspice.')

    # Evita saturação silenciosa no ADC
    fora_faixa = np.count_nonzero((v_adc < 0) | (v_adc >= 4.096))
    if fora_faixa:
        print(f'Aviso: {fora_faixa} amostras fora da faixa do ADC (0 a 4,096 V).')

    # Recupera os codigos de 12 bits ja definidos no LTspice (passos de 1 mV)
    codigo_adc = np.clip(np.rint(v_adc / 0.001), 0, 4095).astype(np.int16)
    # Retira apenas o offset DC nominal medido no circuito (1,992 V)
    offset_adc_v=1.992
    codigo_offset = int(round(offset_adc_v / 0.001))
    valores_int16 = (codigo_adc.astype(np.int32) - codigo_offset).astype(np.int16)

    pasta = os.path.join(nome_saida, 'continuous', 'EMG-SIM-2.0')
    os.makedirs(pasta, exist_ok=True)
    valores_int16.tofile(os.path.join(pasta, 'continuous.dat'))

    # Timestamps em int64 como no sample data do Open Ephys GUI
    contadores = np.arange(1, len(t_adc) + 1, dtype=np.int64)
    np.save(os.path.join(pasta, 'timestamps.npy'), contadores)
    np.save(os.path.join(pasta, 'sample_numbers.npy'), contadores)

    # Metadados formatados seguindo o sample data do Open Ephys GUI
    metadata = {
        'GUI version': '0.4.5',  # estrutura do exemplo que funcionou no GUI 1.0.x
        'continuous': [{
            'folder_name': 'EMG-SIM-2.0/',
            'sample_rate': FS_ADC,
            'source_processor_name': 'LTSpice Simulator',
            'source_processor_id': 100,
            'source_processor_sub_idx': 0,
            'recorded_processor': 'LTSpice Simulator',
            'recorded_processor_id': 100,
            'num_channels': 1,
            'channels': [{
                'channel_name': 'CH0',
                'description': 'V(LOGGER-CF), sem alterar amplitude; offset DC nominal retirado',
                'identifier': 'genericdata.continuous',
                'history': 'LTSpice Simulator',
                'bit_volts': 2.5, #assumindo ganho de ~400x no circuito, 1 bit ~ 2.5 uV na escala do OE
                'units': 'uV',
                'source_processor_index': 0,
                'recorded_processor_index': 0
            }]
        }],
        'events': [],
        'spikes': []
    }
    with open(os.path.join(nome_saida, 'structure.oebin'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f'{len(valores_int16)} amostras convertidas a {FS_ADC} Hz.')
    print(f'Arquivos em: {nome_saida}.')


def main():
    print('\nSIMULADOR EMG')
    print('1 - Gerar simulação em .txt para entrada no LTspice')
    print('2 - Converter .txt de saída do LOGGER (LTSpice) em .dat para leitura no Open Ephys.')
    escolha = input('Escolha 1 ou 2: ').strip()

    if escolha == '1':
        emg_simulator()
    elif escolha == '2':
        arquivo = input('Título do .txt exportado do LTSpice: ').strip().strip('"')
        arquivopath = os.path.join(os.getcwd(), arquivo)
        if not os.path.isfile(arquivopath):
            print(f'Arquivo {arquivo} não encontrado no diretório atual.')
            return
        pasta = input('Nome da pasta de saída do .dat para OpenEphys: ').strip()
        if not pasta:
            pasta = 'Simulacao_OpenEphys'
        txt2dat_emg(ltsp_file=arquivopath, inicio_s=0.5, nome_saida=pasta)
    else:
        print('Opcao invalida. Execute novamente e escolha 1 ou 2.')



# 2. TESTES BÁSICOS:
a, b = muap_gen(FS, 1, depth_mm=5, amp_uv=20, lambda_val=1.0)
try:
    assert len(a) == len(b) == 200
    assert round(DISTANCIA_ELETRODOS_MM / VELOCIDADE_MM_S * FS) == 50
    assert np.max(np.abs(a)) > 0
except AssertionError:
    print('O teste de importação falhou e é necessário debugar.')



# 3. EXECUÇÃO:
if __name__ == "__main__":
    main()
