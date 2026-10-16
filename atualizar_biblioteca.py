import json
import requests

# Nome do arquivo da base de dados
ARQUIVO_JSON = "livros.json"


def buscar_dados_isbn(isbn):
  # Limpa traços ou espaços do ISBN
  isbn_limpo = isbn.replace("-", "").strip()
  url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_limpo}"

  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      if "items" in data:
        info = data["items"][0]["volumeInfo"]
        return {
            "titulo": info.get("title", "Desconhecido"),
            "autores": ", ".join(info.get("authors", ["Desconhecido"])),
            "editora": info.get("publisher", "Não informada"),
            "ano": info.get("publishedDate", "Não informado")[:4],  # Pega só o ano
            "capa": info.get("imageLinks", {}).get("thumbnail", ""),
        }
  except Exception as e:
    print(f"Erro ao buscar ISBN {isbn}: {e}")

  return None


def main():
  with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
    livros = json.load(f)

  atualizado = False

  for livro in livros:
    # Se o livro tem ISBN mas o título está vazio, busca os dados
    if livro.get("isbn") and not livro.get("titulo"):
      print(f"Buscando dados para o ISBN: {livro['isbn']}...")
      dados = buscar_dados_isbn(livro["isbn"])
      if dados:
        livro.update(dados)
        atualizado = True

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados atualizada com sucesso!")
  else:
    print("Nenhum livro novo para atualizar.")


if __name__ == "__main__":
  main()
