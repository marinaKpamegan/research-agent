from langchain_community.vectorstores import FAISS

class FaissService:
    def __init__(self):
        self.vectorstore = None

    # 1. Création et sauvegarde initiale
    def create_and_save_index(self, documents, embeddings, index_path="faiss_index"):
        vectorstore = FAISS.from_documents(documents, embeddings)
        vectorstore.save_local(index_path)
    print("Index sauvegardé localement.")

# 2. Chargement pour utilisation ultérieure
def load_index(embeddings, index_path="faiss_index"):
    # allow_dangerous_deserialization=True est requis pour charger des fichiers pickle localement
    vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    return vectorstore

#     retriever = vectorstore.as_retriever(
#     search_type="mmr",
#     search_kwargs={'k': 5, 'fetch_k': 20} # Analyse 20 docs, en garde 5 diversifiés
# )