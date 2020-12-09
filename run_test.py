import subprocess
import os

FILE_NAME_CANS = "cans-image-urls.txt"
FILE_NAME_TRASH = "trash-image-urls.txt"

def runCommands(c):
    responses = []
    #grab each url; run generate hash from image url command; then run command to verifies if hashed file
    for url in c:
        args_hg = ['python3', 'rest/rest-client.py', '0.0.0.0:5000', 'url', url, '1']
        hash_gen = subprocess.Popen(args_hg, stdout=subprocess.PIPE)
        try:
            out, err = hash_gen.communicate(timeout=10)
        except TimeoutExpired:
            hash_gen.kill()
            out, err = hash_gen.communicate()

        url_hash = out.decode("utf-8").split('\'')[3]

        #run check hash
        args_ch = ['python3', 'rest/rest-client.py', '0.0.0.0:5000', 'check', url_hash, '1']
        check_hash = subprocess.Popen(args_ch, stdout=subprocess.PIPE)
        try:
            out2, err2 = check_hash.communicate(timeout=10)
        except TimeoutExpired:
            check_hash.kill()
            out2, err2 = check_hash.communicate()

        responses.append(out2.decode("utf-8").split('\'')[3])
    return responses

with open(FILE_NAME_CANS) as f:
    content = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content = [x.strip() for x in content]

with open(FILE_NAME_TRASH) as f:
    content2 = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content2 = [x.strip() for x in content2]

recyclables = runCommands(content)
trash = runCommands(content2)

count = 0
for res in recyclables:
    if res == 'yes':
        count += 1
print('Hit rate of can test images is %.2f' % (count / len(recyclables)))

count2 = 0
for res in trash:
    if res == 'yes':
        count2 += 1
print('Hit rate of trash test images is %.2f' % (count2 / len(trash)))
