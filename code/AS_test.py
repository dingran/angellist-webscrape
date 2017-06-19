import AngelScraper as AS

a = AS.AngelScraper()

a.generate_url_list(False)
a.parse_all_index_pages()