import urllib.request

opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)
with open('../country_list.csv', encoding='utf8') as file:
    for line in file:
        line = line.rstrip()
        line = line.split(',')
        subline = line[2].split(' ')
        url = ('https://www.countries-ofthe-world.com/flags-normal/flag-of-' +
                '-'.join(subline) + '.png')
        title = line[2] + ' - ' + 'flag.jpg'

        
        urllib.request.urlretrieve(url, title)
