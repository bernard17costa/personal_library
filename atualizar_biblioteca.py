import json
import requests

ARQUIVO_JSON = "livros.json"


def isbn13_para_isbn10(isbn13):
  """Converte um ISBN-13 com prefixo 978 para ISBN-10 calculando o dígito verificador mod 11."""
  limpo = "".join(ch for ch in str(isbn13) if ch.isdigit())
  if len(limpo) != 13 or not limpo.startswith("978"):
    return None

  corpo = limpo[3:12]
  soma = sum((10 - i) * int(digito) for i, digito in enumerate(corpo))
  resto = (11 - (soma % 11)) % 11
  digito_verificador = "X" if resto == 10 else str(resto)
  return corpo + digito_verificador


def formatar_multiplos_nomes(string_nomes):
  if not string_nomes:
    return ""
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


def buscar_google_books(codigo_isbn):
  url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{codigo_isbn}"
  try:
    response = requests.get(url, timeout=10)
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


def buscar_open_library(codigo_isbn):
  url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{codigo_isbn}&jscmd=data&format=json"
  try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json()
      chave = f"ISBN:{codigo_isbn}"
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


def buscar_em_apis(codigo_isbn):
  dados = buscar_google_books(codigo_isbn)
  if dados and (dados["titulo"] or dados["capa"]):
    return dados

  dados_ol = buscar_open_library(codigo_isbn)
  if dados_ol and (dados_ol["titulo"] or dados_ol["capa"]):
    return dados_ol

  return None


def buscar_dados_isbn(isbn):
  isbn_limpo = "".join(ch for ch in str(isbn) if ch.isalnum()).strip()

  # 1. Busca direta com o ISBN informado (geralmente ISBN-13)
  dados = buscar_em_apis(isbn_limpo)
  if dados:
    return dados

  # 2. Fallback para ISBN-10 quando aplicável (ISBN-13 iniciado por 978)
  isbn10 = isbn13_para_isbn10(isbn_limpo)
  if isbn10 and isbn10 != isbn_limpo:
    print(f"-> Tentando fallback com ISBN-10: {isbn10}...")
    dados_10 = buscar_em_apis(isbn10)
    if dados_10:
      return dados_10

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

          if not str(livro.get("autor", "")).strip() and dados.get("autor"):
            livro["autor"] = dados["autor"]

          if not str(livro.get("editora", "")).strip() and dados.get("editora"):
            livro["editora"] = dados["editora"]

          if not str(livro.get("publicacao", "")).strip() and dados.get(
              "publicacao"
          ):
            livro["publicacao"] = dados["publicacao"]

          if not str(livro.get("lingua", "")).strip() and dados.get("lingua"):
            livro["lingua"] = dados["lingua"]

          if dados.get("capa"):
            livro["capa"] = dados["capa"]

          livro["titulo original"] = livro.get("titulo original", "")
          livro["tradutor"] = livro.get("tradutor", "")
          livro["impressao"] = livro.get("impressao", "")
          livro["edicao"] = livro.get("edicao", "")
          livro["emprestado"] = livro.get("emprestado", "")

          atualizado = True
          print(f"-> Sucesso para o ISBN: {isbn}")
        else:
          print(f"-> Aviso: ISBN {isbn} não encontrado nas APIs.")

      autor_atual = str(livro.get("autor", "")).strip()
      if autor_atual and "," not in autor_atual:
        livro["autor"] = formatar_multiplos_nomes(autor_atual)
        atualizado = True

      tradutor_atual = str(livro.get("tradutor", "")).strip()
      if tradutor_atual and "," not in tradutor_atual:
        livro["tradutor"] = formatar_multiplos_nomes(tradutor_atual)
        atualizado = True

  if atualizado:
    with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
      json.dump(livros, f, ensure_ascii=False, indent=4)
    print("Base de dados atualizada com sucesso!")
  else:
    print("Nenhum livro precisou de atualização.")


if __name__ == "__main__":
  main()
