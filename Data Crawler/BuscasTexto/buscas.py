import pymysql
import nltk

def calculaPageRank(iteracoes):
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice', autocommit = True)
    cursorLimpaTabela = conexao.cursor()
    cursorLimpaTabela.execute('delete from page_rank')
    cursorLimpaTabela.execute('insert into page_rank select idurl, 1.0 from urls')
    for i in range(iteracoes):
        print("Iteração " + str(i + 1))
        cursorUrl = conexao.cursor()
        cursorUrl.execute('select idurl from urls')
        for url in cursorUrl:
            #print(url[0])
            pr = 0.15
            
            cursorLinks = conexao.cursor()
            cursorLinks.execute('select distinct(idurl_origem) from url_ligacao where idurl_destino = %s', url[0])
            for link in cursorLinks:
                cursorPageRank = conexao.cursor()
                cursorPageRank.execute('select nota from page_rank where idurl = %s', link[0])
                linkPageRank = cursorPageRank.fetchone()[0]
                cursorQuantidade = conexao.cursor()
                cursorQuantidade.execute('select count(*) from url_ligacao where idurl_origem = %s', link[0])
                linkQuantidade = cursorQuantidade.fetchone()[0]
                pr += 0.85 * (linkPageRank / linkQuantidade)
            cursorAtualiza = conexao.cursor()
            cursorAtualiza.execute('update page_rank set nota = %s where idurl = %s', (pr, url[0]))
                
    cursorAtualiza.close()
    cursorQuantidade.close()    
    cursorPageRank.close()
    cursorUrl.close()
    cursorLinks.close()
    cursorLimpaTabela.close()
    conexao.close()

#calculaPageRank(20)

def getUrl(idurl):
    retorno = ''
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    cursor.execute('select url from urls where idurl = %s', idurl)
    if cursor.rowcount > 0:
        retorno = cursor.fetchone()[0]
    cursor.close()
    conexao.close()
    return retorno

#getUrl(2)
    
def normalizaMaior(notas):
    menor = 0.00001
    maximo = max(notas.values())
    if maximo == 0:
        maximo = menor
    return dict([(id, float(nota) / maximo) for (id, nota) in notas.items()])

def normalizaMenor(notas):
    menor = 0.00001
    minimo = min(notas.values())
    return dict([(id, float(minimo) / max(menor, nota)) for (id, nota) in notas.items()])

'''minimo = 5
50 10
5 / 50 = 0,1
5 / 10 = 0,5'''
    
def frequenciaScore(linhas):
    contagem = dict([(linha[0], 0) for linha in linhas])
    for linha in linhas:
        #print(linha)
        contagem[linha[0]] += 1
    
    return normalizaMaior(contagem)

def localizacaoScore(linhas):
    localizacoes = dict([linha[0], 1000000] for linha in linhas)
    for linha in linhas:
        #print(linha)
        soma = sum(linha[1:])
        if soma < localizacoes[linha[0]]:
            localizacoes[linha[0]] = soma
    return normalizaMenor(localizacoes)

def distanciaScore(linhas):
    if len(linhas[0]) <= 2:
        return dict([(linha[0], 1.0) for linha in linhas])
    distancias = dict([(linha[0], 1000000) for linha in linhas])
    for linha in linhas:
        dist = sum([abs(linha[i] - linha[i - 1]) for i in range(2, len(linha))])
        if dist < distancias[linha[0]]:
            distancias[linha[0]] = dist
    return normalizaMenor(distancias)

def contagemLinkScore(linhas):
    contagem = dict([linha[0], 1.0] for linha in linhas)
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    for i in contagem:
        #print(i)
        cursor.execute('select count(*) from url_ligacao where idurl_destino = %s', i)
        contagem[i] = cursor.fetchone()[0]
    
    cursor.close()
    conexao.close()
    return normalizaMaior(contagem)

def pageRankScore(linhas):
    pageranks = dict([linha[0], 1.0] for linha in linhas)
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    for i in pageranks:
        cursor.execute('select nota from page_rank where idurl = %s', i)
        pageranks[i] = cursor.fetchone()[0]
    
    cursor.close()
    conexao.close()
    return normalizaMaior(pageranks)

def textoLinkScore(linhas, palavrasid):
    contagem = dict([linha[0], 0] for linha in linhas)
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    for id in palavrasid:
        cursor = conexao.cursor()
        cursor.execute('select ul.idurl_origem, ul.idurl_destino from url_palavra up inner join url_ligacao ul on ul.idurl_ligacao = up.idurl_ligacao and up.idpalavra = %s', id)
        for (idurl_origem, idurl_destino) in cursor:
            if idurl_destino in contagem:
                cursorRank = conexao.cursor()
                cursorRank.execute('select nota from page_rank where idurl = %s', idurl_origem)
                pr = cursorRank.fetchone()[0]
                contagem[idurl_destino] += pr
    
    cursorRank.close()
    cursor.close()
    conexao.close()
    return normalizaMaior(contagem)

# procura links que contenham as palavras de busca
# se o alvo do link for algum dos documentos encontrados na busca, a nota pagerank
# da origem do link é somada à nota final desse resultado. Uma página com muitos links
# que contenham os termos de consulta vindos de páginas importantes terá nota maior
#textoLinkScore(linhas, palavrasid)  

linhas, palavrasid = buscaMaisPalavras('python programação')
teste = distanciaScore(linhas)

def pesquisa(consulta):
    # 1
    linhas, palavrasid = buscaMaisPalavras(consulta)
    
    # MUDAR AQUI
    scores = textoLinkScore(linhas, palavrasid)
    #scores = pageRankScore(linhas)
    #scores = contagemLinkScore(linhas)
    #scores = frequenciaScore(linhas)
    #scores = localizacaoScore(linhas)
    #scores = distanciaScore(linhas)
    
    #scores = dict([linha[0], 0] for linha in linhas)
    
    #for url, score in scores.items():
    #    print(str(url) + ' - ' + str(score))
    
    # 2
    scoresordenado = sorted([(score, url) for (url, score) in scores.items()], reverse = 1)
    for (score, idurl) in scoresordenado[0:10]:
        print('%f\t%s' % (score, getUrl(idurl)))
        
# 3
pesquisa('python programação')

def pesquisaPeso(consulta):
    linhas, palavrasid = buscaMaisPalavras(consulta)
    totalscores = dict([linha[0], 0] for linha in linhas)
    
    pesos = [(1.0, frequenciaScore(linhas)),
             (1.0, localizacaoScore(linhas)),
             (1.0, distanciaScore(linhas)),
             (1.0, contagemLinkScore(linhas)),
             (5.0, pageRankScore(linhas)),
             (1.0, textoLinkScore(linhas, palavrasid))]
    
    for (peso, scores) in pesos:
        #print(peso)
        #print(scores)
        for url in totalscores:
            #print(url)
            totalscores[url] += peso * scores[url]
    
    scoresordenado = sorted([(score, url) for (url, score) in totalscores.items()], reverse = 1)
    for (score, idurl) in scoresordenado[0:10]:
        print('%f\t%s' % (score, getUrl(idurl)))       
    
pesquisaPeso('python programação')

def buscaMaisPalavras(consulta):
    listacampos = 'p1.idurl'
    listatabelas = ''
    listaclausulas = ''
    palavrasid = []
    
    palavras = consulta.split(' ')
    numerotabela = 1
    for palavra in palavras:
        idpalavra = getIdPalavra(palavra)
        if idpalavra > 0:
            palavrasid.append(idpalavra)
            if numerotabela > 1:
                listatabelas += ', '
                listaclausulas += ' and '
                listaclausulas += 'p%d.idurl = p%d.idurl and ' % (numerotabela - 1, numerotabela)
            listacampos += ', p%d.localizacao' % numerotabela
            listatabelas += ' palavra_localizacao p%d' % numerotabela
            listaclausulas += 'p%d.idpalavra = %d' % (numerotabela, idpalavra)
            numerotabela += 1
    consultacompleta = 'select %s from %s where %s' % (listacampos, listatabelas, listaclausulas)
    
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    cursor.execute(consultacompleta)
    linhas = [linha for linha in cursor]
    cursor.close()
    conexao.close()
    
    return linhas, palavrasid
            
buscaMaisPalavras('python programação')

def getIdPalavra(palavra):
    retorno = -1
    stemmer = nltk.stem.RSLPStemmer()
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    cursor.execute('select idpalavra from palavras where palavra = %s', stemmer.stem(palavra))
    if cursor.rowcount > 0:
        retorno = cursor.fetchone()[0]
    cursor.close()
    conexao.close()
    return retorno

#getIdPalavra('programação')

def buscaSimples(palavra):
    idpalavra = getIdPalavra(palavra)
    conexao = pymysql.connect(host='localhost', user='root', passwd='123456', db='indice')
    cursor = conexao.cursor()
    cursor.execute('select urls.url from palavra_localizacao plc inner join urls on plc.idurl = urls.idurl where plc.idpalavra = %s', idpalavra)
    paginas = set()
    for url in cursor:
        #print(url[0])
        paginas.add(url[0])
        
    print('Páginas encontradas: ' + str(len(paginas)))
    for url in paginas:
        print(url)
    
    cursor.close()
    conexao.close()
    
#buscaSimples('programação')