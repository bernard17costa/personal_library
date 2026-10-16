import json
import requests

ARQUIVO_JSON = "livros.json"


def buscar_google_books(isbn_limpo):
  url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_limpo}"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      if "items" in data:
        info = data["items"][0]["volumeInfo"]
        return {
            "titulo": info.get("title", ""),
            "autor": ", ".join(info.get("authors", [])),
            "editora": info.get("publisher", ""),
            "publicacao": info.get("publishedDate", ""),
            "lingua": info.get("language", "").upper(),
            "capa": info.get("imageLinks", {}).get("thumbnail", ""),
        }
  except Exception:
    pass
  return None


def buscar_open_library(isbn_limpo):
  url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_limpo}&jscmd=data&format=json"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      chave = f"ISBN:{isbn_limpo}"
      if chave in data:
        info = data[chave]
        autores = ", ".join([a.get("name", "") for a in info.get("authors", [])])
        editoras = ", ".join(
            [e.get("name", "") for e in info.get("publishers", [])]
        )
        capa = info.get("cover", {}).get("medium", "")
        return {
            "titulo": info.get("title", ""),
            "autor": autores,
            "editora": editoras,
            "publicacao": info.get("publish_date", ""),
            "lingua": "",
            "capa": capa,
        }
  except Exception:
    pass
  return None


def buscar_dados_isbn(isbn):
  isbn_limpo = isbn.replace("-", "").strip()

  # 1. Tenta o Google Books
  dados = buscar_google_books(isbn_limpo)
  if dados and (dados["titulo"] or dados["capa"]):
    return dados

  # 2. Se não achar, tenta a Open Library
  dados_ol = buscar_open_library(isbn_limpo)
  if dados_ol and (dados_ol["titulo"] or dados_ol["capa"]):
    return dados_ol

  return None


def main():
  try:
    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
      livros = json.load(f)
  except FileNotFoundError:
    print(f"Arquivo {ARQUIVO_JSON} não encontrado.")
    return

  atualizado = False

  for livro in livros:
    isbn = livro.get("isbn")
    if isbn:
      # Verifica se o título está vazio OU se a capa está faltando/vazia
      titulo_vazio = not str(livro.get("titulo", "")).strip()
      capa_vazia = not str(livro.get("capa", "")).strip()

      if titulo_vazio or capa_vazia:
        print(f"Buscando dados/capa para o ISBN: {isbn}...")
        dados = buscar_dados_isbn(isbn)

        if dados:
          # Se o título estava vazio, preenche. Se já tinha, mantém o que estava.
          if titulo_vazio and dados["titulo"]:
            livro["titulo"] = dados["titulo"]

          # Se o autor estava vazio, preenche.
          if not str(livro.get("autor", "")).strip() and dados["autor"]:
            livro["autor"] = dados["autor"]

          # Se a editora estava vazia, preenche.
          if not str(livro.get("editora", "")).strip() and dados["editora"]:
            livro["editora"] = dados["editora"]

          # Se a publicação estava vazia, preenche.
          if (
              not str(livro.get("publicacao", "")).strip()
              and dados["publicacao"]
          ):
            livro["publicacao"] = dados["publicacao"]

          # Se a língua estava vazia, preenche.
          if not str(livro.get("lingua", "")).strip() and dados.get("lingua"):
            livro["lingua"] = dados["lingua"]

          # ATUALIZA A CAPA SEMPRE QUE ENCONTRAR UMA NOVA NA API
          if dados.get("capa"):
            livro["capa"] = dados["capa"]

          # Garante a integridade dos campos manuais
          livro["titulo original"] = livro.get("titulo original", "")
          livro["tradutor"] = livro.get("tradutor", "")
          livro["impressao"] = livro.get("impressao", "")
          livro["edicao"] = livro.get("edicao", "")
          livro["emprestado"] = livro.get("emprestado", "")

          atualizado = True
          print(f"-> Atualizado com sucesso para o ISBN: {isbn}")
        else:
          print(f"-> Aviso: Nenhuma API encontrou dados para o ISBN {isbn}.")

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados e capas atualizadas com sucesso!")
  else:
    print("Nenhum livro novo precisou de atualização.")


if __name__ == "__main__":
  main()
