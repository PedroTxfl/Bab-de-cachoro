import cv2
import numpy as np

TINY = False

ARQUIVO_CFG = "yolov3{}.cfg".format("-tiny" if TINY else "")
ARQUIVO_PESOS = "yolov3{}.weights".format("-tiny" if TINY else "")
ARQUIVO_CLASSES = "coco{}.names".format("-tiny" if TINY else "")

with open(ARQUIVO_CLASSES, "r") as arquivo:
    CLASSES = [linha.strip() for linha in arquivo.readlines()]

CORES = np.random.uniform(0, 255, size=(len(CLASSES), 3))

def carregar_modelo_pretreinado():
    modelo = cv2.dnn.readNetFromDarknet(ARQUIVO_CFG, ARQUIVO_PESOS)
    modelo.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    modelo.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    if modelo.empty():
        raise IOError("Não foi possível carregar o modelo de detecção de objetos.")
    return modelo

def preprocessar_frame(frame):
    blob = cv2.dnn.blobFromImage(frame, scalefactor=1/255.0, size=(416, 416), swapRB=True, crop=False)
    return blob

def detectar_objetos(frame, modelo):
    blob = preprocessar_frame(frame)
    modelo.setInput(blob)
    nomes_camadas = modelo.getLayerNames()
    camadas_saida = [nomes_camadas[i - 1] for i in modelo.getUnconnectedOutLayers()]
    saidas = modelo.forward(camadas_saida)
    return saidas

def desenhar_deteccoes(frame, deteccoes, limiar=0.5):
    (altura, largura) = frame.shape[:2]
    caixas = []
    confiancas = []
    ids_classes = []

    for saida in deteccoes:
        for deteccao in saida:
            pontuacoes = deteccao[5:]
            id_classe = np.argmax(pontuacoes)
            confianca = pontuacoes[id_classe]
            if confianca > limiar and CLASSES[id_classe] == "cachorro":
                caixa = deteccao[0:4] * np.array([largura, altura, largura, altura])
                (centroX, centroY, largura_caixa, altura_caixa) = caixa.astype("int")
                x = int(centroX - (largura_caixa / 2))
                y = int(centroY - (altura_caixa / 2))

                caixas.append([x, y, int(largura_caixa), int(altura_caixa)])
                confiancas.append(float(confianca))
                ids_classes.append(id_classe)

    indices = cv2.dnn.NMSBoxes(caixas, confiancas, limiar, limiar - 0.1)
    
    region_polygon = np.array([[0, 580], [1000, 350], [1600, 800], [0, 800]])

    if len(indices) > 0:
        for i in indices.flatten():
            (x, y) = (caixas[i][0], caixas[i][1])
            (largura_caixa, altura_caixa) = (caixas[i][2], caixas[i][3])
            cor = [int(c) for c in CORES[ids_classes[i]]]
            cv2.rectangle(frame, (x, y), (x + largura_caixa, y + altura_caixa), cor, 2)
            texto = f"{CLASSES[ids_classes[i]]}: {confiancas[i]:.2f}"
            cv2.putText(frame, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

            centro_cachorro = (x + largura_caixa // 2, y + altura_caixa // 2)
            if cv2.pointPolygonTest(region_polygon, centro_cachorro, False) < 0:
                print("Alerta! Cachorro fugiu!")

def main():
    print("Inicializando o sistema...")
    modelo = carregar_modelo_pretreinado()

    ARQUIVO_VIDEO = "dog_fugindo.mp4"  
    captura_video = cv2.VideoCapture(ARQUIVO_VIDEO)

    if not captura_video.isOpened():
        raise Exception("Não foi possível abrir o arquivo de vídeo.")

    limiar_confianca = 0.4

    try:
        while True:
            ret, frame = captura_video.read()
            if not ret:
                break
            
            deteccoes = detectar_objetos(frame, modelo)
            desenhar_deteccoes(frame, deteccoes, limiar_confianca)

            cv2.polylines(frame, [np.array([[0, 580], [1000, 350], [1600, 800], [0, 800]])], isClosed=True, color=(0, 255, 0), thickness=2)

            cv2.imshow('Detecta Objetos', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        captura_video.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
