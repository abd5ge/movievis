import json
import csv
import os


def convert_to_csv(inputfile, output_dir):
    d = []

    # with open('all_mapped_movies.json') as f: # Output of processed scripts
    with open(inputfile, encoding='utf-8') as f: # Output of processed scripts
            d.append(json.load(f))
        

    dfilt = lambda x, y: dict([ (i,x[i]) for i in x if i in set(y) ])

    ## Script parsed meta data from IMSDB
    keys = ["row_id","id","title", "writers", "description", "link", "tmdb_id", "file", "characters"]
    with open(os.path.join(output_dir,'completed_script_info.tsv'), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        for i in range(len(d)):
            cnt = 1
            for j in range(len(d[i])):
                filt_by_keys = ("id","title", "writers", "description", "link", "tmdb_id", "file", "characters")
                result = dfilt(d[i][j], filt_by_keys)
                combined = {**result,**{'row_id':cnt}}
                writer.writerow(combined)
                cnt +=1

    ## Character metadata parsed from scripts
    keys = ["id", "tmdb_id","characters"]
    with open(os.path.join(output_dir,'completed_script_char_info.tsv'), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        for i in range(len(d)):
            cnt = 1
            for j in range(len(d[i])):
                #print(d[i][0].keys())
                filt_by_keys = ("tmdb_id","characters")
                result = dfilt(d[i][j], filt_by_keys)
                #writer.writerow(result)
                for list_val in result['characters']:
                    writer.writerow({'id':cnt, 'tmdb_id': result['tmdb_id'], 'characters': list_val})
                    cnt += 1

    ## Scene info parsed from scripts. Starts at MIN scene from dialogue dict
    keys = ['id', "tmdb_id","scene_id", "scenes"]
    with open(os.path.join(output_dir,'completed_script_scene_info.tsv'), 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        for i in range(len(d)):
            cnt = 0
            start = d[0][0]['dialog'][0]['scene']
            for j in range(len(d[i])):
                #print(d[i][0].keys())
                filt_by_keys = ("tmdb_id","scenes")
                result = dfilt(d[i][j], filt_by_keys)
                #writer.writerow(result)
                scene_cnt = start
                for list_val in result['scenes']:  
                    writer.writerow({'id': cnt, 'tmdb_id': result['tmdb_id'],'scene_id':scene_cnt, 'scenes': list_val})
                    scene_cnt += 1
                    cnt += 1

    # Characters that were found from script parsing         
    keys = ['id', 'tmdb_id', 'found_char','celeb_id','actual_full_name', 'character_order', 'actual_name', 'similarity']  
    with open(os.path.join(output_dir,'completed_script_mapped_char_info.tsv'), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        try:
            for i in range(len(d)):
                cnt = 1
                for j in range(len(d[i])):
                    for k in d[i][j]['char_map']:
                        a = {'found_char':k}
                        b = d[i][j]['char_map'][k]
                        c = {'tmdb_id': d[i][j]['tmdb_id']}
                        combined ={**a,**b,**{'id':cnt},**c}
                        writer.writerow(combined)
                        cnt += 1
        except:
            pass

                    
    # Character dialogue found from script parsing            
    keys = ['id', 'tmdb_id', 'celeb_id', 'character', 'line', 'scene', 'line_number']  
    with open(os.path.join(output_dir,'completed_script_dialog_info.tsv'), 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys, delimiter='\t')
        writer.writeheader()
        for i in range(len(d)):
            cnt = 1
            for j in range(len(d[i])):
                for k in d[i][j]['dialog']:
                    c = {'tmdb_id': d[i][j]['tmdb_id']}
                    combined = {**k,**{'id':cnt}, **c}
                    writer.writerow(combined)
                    cnt += 1
