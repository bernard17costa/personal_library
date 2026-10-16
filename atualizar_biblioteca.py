import json
import requests

ARQUIVO_JSON = "livros.json"


def buscar_dados_isbn(isbn):
  isbn_limpo = isbn.replace("-", "").strip()
  url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_limpo}"

  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      if "items" in data:
        info = data["items"][0]["volumeInfo"]
        return {
            "titulo": info.get("title", ""),
            "titulo original": "",
            "autor": ", ".join(info.get("authors", [])),
            "tradutor": "",
            "editora": info.get("publisher", ""),
            "publicacao": info.get("publishedDate", ""),
            "impressao": "",
            "edicao": "",
            "lingua": info.get("language", "").upper(),
            "emprestado": "",
            "capa": info.get("imageLinks", {}).get("thumbnail", ""),
        }
  except Exception as e:
    print(f"Erro ao buscar ISBN {isbn}: {e}")

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
    # Verifica se o título está vazio (considerando espaços em branco)
    if livro.get("isbn") and not str(livro.get("titulo", "")).strip():
      print(f"Buscando dados para o ISBN: {livro['isbn']}...")
      dados = buscar_dados_isbn(livro["isbn"])
      if dados:
        livro["titulo"] = dados["titulo"]
        livro["autor"] = dados["autor"]
        livro["editora"] = dados["editora"]
        livro["publicacao"] = dados["publicacao"]
        livro["lingua"] = dados["lingua"]
        livro["titulo original"] = livro.get("titulo original", "")
        livro["tradutor"] = livro.get("tradutor", "")
        livro["impressao"] = livro.get("impressao", "")
        livro["edicao"] = livro.get("edicao", "")
        livro["emprestado"] = livro.get("emprestado", "")
        livro["capa"] = dados["capa"]
        atualizado = True
      else:
        print(f"Nenhum dado encontrado na API para o ISBN {livro['isbn']}.")

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados atualizada com sucesso!")
  else:
    print("Nenhum livro novo para atualizar.")


if __name__ == "__main__":
  main()
