from plover import log

def prioritize_dictionaries(selections, old_file_names):
    def match_partial_path(file_names, selection):
        matches = []
        for file_name in file_names:
            if file_name.endswith(selection):
                matches.append(file_name)

        if matches:
            matches.sort(key=len)
            return(matches[0])

    selections = [x.strip() for x in selections.split(";")]
    selections.reverse()
    new_file_names = old_file_names[:]
    for selection in selections:
        matching_file = match_partial_path(old_file_names, selection)
        if matching_file:
            ix = new_file_names.index(matching_file)
            t = new_file_names.pop(ix)
            new_file_names.append(t)
        else:
            log.error('No dictionary file matching "%s" found.' % selection, exc_info=True)
        
    return new_file_names     

