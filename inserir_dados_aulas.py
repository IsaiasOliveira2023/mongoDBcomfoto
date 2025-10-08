from pymongo import MongoClient
from gridfs import GridFS
from pymongo.errors import ConnectionFailure, OperationFailure
import os

# --- 1. Sua String de Conexão ---
MONGO_URI = "cole aqui "

# --- 2. Nome do Database e da Collection ---
DATABASE_NAME = "aulasADS"
COLLECTION_NAME = "alunos"

# Mapeamento: aluno['matricula'] -> nome da imagem local
IMAGENS_ALUNOS = {
    "2023001": "ana.jpg",         # Ana Silva
    "2023002": "bruno.jpg",       # Bruno Mendes
    "2023003": "carla.jpg",       # Carla Oliveira
    "2023004": "daniel.jpg"       # Daniel Costa
}

def inserir_documentos_alunos_com_fotos():
    client = None
    try:
        print(f"Conectando ao MongoDB Atlas no database '{DATABASE_NAME}'...")
        client = MongoClient(MONGO_URI)

        # Testa conexão
        client.admin.command('ping')
        print("✅ Conexão estabelecida com sucesso!")

        # Acessa o banco de dados
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        fs = GridFS(db)  # Instância do GridFS para arquivos

        # Lista de documentos modificada para incluir foto_id
        documentos_para_inserir = []

        # --- 1. Prepara os documentos dos alunos com foto_id ---
        documento_aluno_1 = {
            "nome": "Ana Silva",
            "matricula": "2023001",
            "curso": "Análise e Desenvolvimento de Sistemas",
            "fase": 5,
            "disciplinas_atuais": ["Banco de Dados II", "Programação Web"],
            "contato": {
                "email": "ana.silva@aluno.fmp.br",
                "telefone": "48987654321"
            },
            "notas": [
                {"disciplina": "Banco de Dados II", "nota": 8.5},
                {"disciplina": "Programação Web", "nota": 9.0}
            ]
        }

        documento_aluno_2 = {
            "nome": "Bruno Mendes",
            "matricula": "2023002",
            "curso": "Análise e Desenvolvimento de Sistemas",
            "fase": 5,
            "disciplinas_atuais": ["Banco de Dados II", "Engenharia de Software"],
            "contato": {
                "email": "bruno.mendes@aluno.fmp.br",
                "telefone": "48991234567"
            },
            "observacoes": "Participa ativamente das aulas."
        }

        documentos_alunos_novos = [
            {
                "nome": "Carla Oliveira",
                "matricula": "2023003",
                "curso": "Análise e Desenvolvimento de Sistemas",
                "fase": 5,
                "contato": {"email": "carla.ol@aluno.fmp.br"}
            },
            {
                "nome": "Daniel Costa",
                "matricula": "2023004",
                "curso": "Análise e Desenvolvimento de Sistemas",
                "fase": 5,
                "disciplinas_atuais": ["Banco de Dados II"]
            }
        ]

        # Adiciona todos os documentos numa lista única
        todos_os_documentos = [documento_aluno_1, documento_aluno_2] + documentos_alunos_novos

        # --- 2. Salvar imagens no GridFS e adicionar foto_id aos documentos ---
        for aluno in todos_os_documentos:
            matricula = aluno["matricula"]
            caminho_imagem = IMAGENS_ALUNOS.get(matricula)

            if caminho_imagem and os.path.exists(caminho_imagem):
                print(f"🖼️  Salvando imagem '{caminho_imagem}' para {aluno['nome']} no GridFS...")
                with open(caminho_imagem, 'rb') as f:
                    file_id = fs.put(
                        f,
                        filename=f"foto_{matricula}.jpg",
                        content_type="image/jpeg",
                        matricula=matricula,
                        nome_aluno=aluno["nome"]
                    )
                aluno["foto_id"] = file_id  # Adiciona referência ao documento
                print(f"✅ Imagem salva com ID: {file_id}")
            else:
                print(f"⚠️  Imagem não encontrada para {aluno['nome']} (matrícula: {matricula})")

            # Adiciona o aluno modificado à lista final
            documentos_para_inserir.append(aluno)

        # --- 3. Inserção no MongoDB ---
        # Primeiro aluno (individual)
        print(f"\n📥 Inserindo primeiro aluno: {documentos_para_inserir[0]['nome']}...")
        resultado_um = collection.insert_one(documentos_para_inserir[0])
        print(f"✔️  Inserido com _id: {resultado_um.inserted_id}")

        # Demais alunos (em lote)
        restantes = documentos_para_inserir[1:]
        print(f"\n📤 Inserindo {len(restantes)} alunos restantes...")
        resultado_varios = collection.insert_many(restantes)
        print(f"✔️  {len(resultado_varios.inserted_ids)} alunos inseridos.")

        print("\n🎉 Todos os alunos foram inseridos com sucesso, incluindo referências às imagens!")

    except ConnectionFailure as e:
        print(f"❌ Erro de conexão com o MongoDB: {e}")
    except OperationFailure as e:
        errmsg = e.details.get('errmsg', str(e))
        print(f"❌ Erro de operação no MongoDB: {errmsg}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        if client:
            print("🔌 Fechando conexão com o MongoDB.")
            client.close()

# --- EXECUTAR ---
if __name__ == "__main__":

    inserir_documentos_alunos_com_fotos()
