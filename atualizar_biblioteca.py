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
            "lingua": "",  # Open Library dados estruturados variam muito para idioma
            "capa": capa,
        }
  except Exception:
    pass
  return None


def buscar_dados_isbn(isbn):
  isbn_limpo = isbn.replace("-", "").strip()

  # 1. Tenta o Google Books
  dados = buscar_google_books(isbn_limpo)
  if dados and dados["titulo"]:
    return dados

  # 2. Se não achar, tenta a Open Library
  dados_ol = buscar_open_library(isbn_limpo)
  if dados_ol and dados_ol["titulo"]:
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
    if livro.get("isbn") and not str(livro.get("titulo", "")).strip():
      print(f"Buscando dados para o ISBN: {livro['isbn']}...")
      dados = buscar_dados_isbn(livro["isbn"])
      if dados:
        livro["titulo"] = dados["titulo"]
        livro["autor"] = dados["autor"]
        livro["editora"] = dados["editora"]
        livro["publicacao"] = dados["publicacao"]
        if dados.get("lingua"):
          livro["lingua"] = dados["lingua"]
        livro["capa"] = dados["capa"]

        # Garante a existência dos campos opcionais
        livro["titulo original"] = livro.get("titulo original", "")
        livro["tradutor"] = livro.get("tradutor", "")
        livro["impressao"] = livro.get("impressao", "")
        livro["edicao"] = livro.get("edicao", "")
        livro["emprestado"] = livro.get("emprestado", "")

        atualizado = True
        print(f"-> Sucesso encontrado para: {dados['titulo']}")
      else:
        print(
            f"-> Aviso: Nenhuma API pública encontrou o ISBN {livro['isbn']}."
            " Você pode preencher manualmente no JSON se preferir."
        )

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados atualizada com sucesso!")
  else:
    print("Nenhum livro novo para atualizar.")


if __name__ == "__main__":
  main()
