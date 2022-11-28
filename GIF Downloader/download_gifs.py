from urllib import request

file = open("gifs_to_download.txt", "r")
urls = file.readlines()

# Reference: https://stackoverflow.com/questions/41446104/how-do-i-save-a-gif-from-a-url
for i in range(len(urls)):
    request.urlretrieve(urls[i], 'GIFS/GIF-' + str(i) + '.gif')