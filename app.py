from flask import Flask, render_template, request, send_file
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from gridfs import GridFS
from datetime import datetime
from bson.objectid import ObjectId # Necessário para buscar pelo ID do MongoDB
from io import BytesIO # Para manipular a foto na memória antes de enviar ao navegador

# --- 1. Configurações do MongoDB (AS SUAS CONFIGURAÇÕES CORRETAS) ---
MONGO_URI = "mongodb+srv://isaiasoliveira_db_user:Y8mmelSNCRqrhBtl@clusterisaias.y6ccr4r.mongodb.net/aulasADS?retryWrites=true&w=majority&appName=ClusterIsaias"
DATABASE_NAME = "aulasADS"
COLLECTION_NAME = "alunos"

# --- 2. Inicialização do Flask e Conexão ao MongoDB ---
app = Flask(__name__)
client = None
db = None
collection = None
fs = None # Variável para a instância do GridFS

try:
    # Tenta conectar ao MongoDB Atlas uma única vez
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    fs = GridFS(db) # Inicializa o GridFS
    print(f"Flask conectado ao MongoDB Atlas no database '{DATABASE_NAME}' com sucesso!")

except ConnectionFailure as e:
    print(f"ERRO DE CONEXÃO COM O MONGODB: {e}")
except Exception as e:
    print(f"Ocorreu um erro inesperado na inicialização: {e}")
    
# --- 3. Rota para exibir o formulário HTML (Página inicial) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 4. Rota para receber os dados do formulário (POST) e INSERIR ---
@app.route('/submit', methods=['POST'])
def submit_aluno():
    if collection is None: 
        return render_template('index.html', message="Erro: Conexão com MongoDB falhou na inicialização."), 500

    try:
        nome = request.form['nome']
        matricula = request.form['matricula']
        curso = request.form['curso']
        
        # Lógica de Upload e GridFS
        foto_id = None
        foto = request.files.get('foto') 
        
        if foto and foto.filename:
            file_id = fs.put(
                foto,
                filename=foto.filename,
                content_type=foto.content_type,
                matricula=matricula
            )
            foto_id = file_id
            print(f"Foto salva no GridFS para {nome} com ID: {file_id}")
        
        # Cria o documento MongoDB com a referência da foto
        novo_aluno = {
            "nome": nome,
            "matricula": matricula,
            "curso": curso,
            "foto_id": foto_id, 
            "data_cadastro": datetime.now(),
            "origem": "cadastro_web_com_foto"
        }
        
        collection.insert_one(novo_aluno)
        
        return render_template('index.html', message=f"Aluno '{nome}' cadastrado com sucesso!")

    except Exception as e:
        return render_template('index.html', message=f"Erro ao inserir dados: {e}"), 500

# --- 5. Rota para exibir a LISTA de todos os alunos (Nova página) ---
@app.route('/alunos')
def lista_alunos():
    if collection is None: 
        return "Erro: Conexão com MongoDB falhou.", 500
    
    try:
        # Busca TODOS os documentos na coleção 'alunos'
        todos_alunos = list(collection.find().limit(20)) 
        
        # Envia a lista para o template lista.html
        return render_template('lista.html', alunos=todos_alunos)
        
    except Exception as e:
        return f"Erro ao buscar alunos: {e}", 500

# --- 6. Rota para SERVIR (mostrar) a foto salva no GridFS ---
@app.route('/foto/<foto_id>')
def servir_foto(foto_id):
    if fs is None:
        return "Erro: GridFS não inicializado.", 500
    
    try:
        # 1. Converte a string ID para o tipo ObjectId
        file_id = ObjectId(foto_id)
        
        # 2. Busca o arquivo no GridFS
        arquivo_foto = fs.get(file_id)
        
        # 3. Envia o arquivo binário diretamente para o navegador
        return send_file(
            BytesIO(arquivo_foto.read()),
            mimetype=arquivo_foto.content_type,
            as_attachment=False
        )
        
    except Exception:
        return "Foto não encontrada.", 404

# --- 7. Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True)