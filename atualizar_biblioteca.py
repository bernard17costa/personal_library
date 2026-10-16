import json
import requests

ARQUIVO_JSON = "livros.json"


def formatar_multiplos_nomes(string_nomes):
  if not string_nomes:
    return ""

  # Divide caso venha separado por vírgula ou " e "
  nomes = string_nomes.replace(" e ", ", ").split(",")
  nomes_limpos = [n.strip() for n in nomes if n.strip()]

  formatados = []
  for nome_atual in nomes_limpos:
    partes = nome_atual.split()

    if len(partes) > 1 and "," not in nome_atual:
      sobrenome = partes[-1]
      nome = " ".join(partes[:-1])
      formatados.append(f"{sobrenome}, {nome}")
    else:
      formatados.append(nome_atual)

  return "; ".join(formatados)


def buscar_google_books(isbn_limpo):
  url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_limpo}"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      if "items" in data:
        info = data["items"][0]["volumeInfo"]
        autor_bruto = ", ".join(info.get("authors", []))
        return {
            "titulo": info.get("title", ""),
            "autor": formatar_multiplos_nomes(autor_bruto),
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
        autores_lista = [a.get("name", "") for a in info.get("authors", [])]
        autor_bruto = ", ".join(autores_lista)
        editoras = ", ".join(
            [e.get("name", "") for e in info.get("publishers", [])]
        )
        capa = info.get("cover", {}).get("medium", "")
        return {
            "titulo": info.get("title", ""),
            "autor": formatar_multiplos_nomes(autor_bruto),
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

  dados = buscar_google_books(isbn_limpo)
  if dados and (dados["titulo"] or dados["capa"]):
    return dados

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
      titulo_vazio = not str(livro.get("titulo", "")).strip()
      capa_vazia = not str(livro.get("capa", "")).strip()

      if titulo_vazio or capa_vazia:
        print(f"Buscando dados/capa para o ISBN: {isbn}...")
        dados = buscar_dados_isbn(isbn)

        if dados:
          if titulo_vazio and dados["titulo"]:
            livro["titulo"] = dados["titulo"]

          if not str(livro.get("autor", "")).strip() and dados["autor"]:
            livro["autor"] = dados["autor"]

          if not str(livro.get("editora", "")).strip() and dados["editora"]:
            livro["editora"] = dados["editora"]

          if (
              not str(livro.get("publicacao", "")).strip()
              and dados["publicacao"]
          ):
            livro["publicacao"] = dados["publicacao"]

          if not str(livro.get("lingua", "")).strip() and dados.get("lingua"):
            livro["lingua"] = dados["lingua"]

          if dados.get("capa"):
            livro["capa"] = dados["capa"]

          livro["titulo original"] = livro.get("titulo original", "")
          livro["impressao"] = livro.get("impressao", "")
          livro["edicao"] = livro.get("edicao", "")
          livro["emprestado"] = livro.get("emprestado", "")

          atualizado = True
          print(f"-> Atualizado com sucesso para o ISBN: {isbn}")
        else:
          print(f"-> Aviso: Nenhuma API encontrou dados para o ISBN {isbn}.")

      # Formata o autor para o padrão "Sobrenome, Nome" caso ainda não esteja
      autor_atual = str(livro.get("autor", "")).strip()
      if autor_atual and "," not in autor_atual:
        livro["autor"] = formatar_multiplos_nomes(autor_atual)
        atualizado = True

      # Formata o tradutor para o padrão "Sobrenome, Nome" caso esteja preenchido e fora do padrão
      tradutor_atual = str(livro.get("tradutor", "")).strip()
      if tradutor_atual and "," not in tradutor_atual:
        livro["tradutor"] = formatar_multiplos_nomes(tradutor_atual)
        atualizado = True

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados, autores e tradutores formatados com sucesso!")
  else:
    print("Nenhum livro precisou de atualização.")


if __name__ == "__main__":
  main()
