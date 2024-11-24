class YamlParser:
    def __init__(self):
        self.states = [ 'DEBUT', 'CLE','TABLEAU', 'LISTE', 'COMMENTAIRE', 'STRING', 'BLOC','FIN_DOC']
        self.current_state = 'DEBUT'
        self.past_state = 'DEBUT'
        self.buffer = ''
        self.current_space = 0
        self.tab = 0
        self.expected_tab = 0
        self.anchors = []
        self.inlist = False
        self.array_indent = None
        
    def process_char(self, char, file):
    # Gestion des débuts et fins de document
        if self.current_state == 'DEBUT' and char in ('-', '.') and self.current_space==0 and self.expected_tab == 0:
            self.buffer += char
            while (char := file.read(1)) and char not in ('\n'):
                if char == '-' or char == '.':
                    self.buffer += char
                else:
                    break
            if self.buffer == '---':
                return self.handle_document_start()
            elif self.buffer == '...':
                return self.handle_document_end()
            elif len(self.buffer) > 3:
                print('Séquence non reconnue.')
                return False
            return True
    #Gestion des différents caractères que nous pouvons rencontrés 
        if char == '\n':
            return self.handle_newline()
        elif char == ' ':
            return self.handle_space()
        elif char == '#':
            return self.handle_comment_start()
        elif char == ':':
            return self.handle_colon()
        elif char == '-':
            return self.handle_dash()
        elif char == '.':
            return self.handle_dot()
        elif char == '|' or char == '>':
            return self.handle_bloc()
        elif char == '&':
            return self.handle_anchor_definition(file)
        elif char == '*':
            return self.handle_anchor_reference(file)   
        else: 
            return self.handle_scalar_char(char)
# Nouvelle ligne (\n)  
    def handle_newline(self):
        if self.current_state == 'BLOC':
            self.current_space = 0
            self.tab = 0
            self.current_state='STRING'
            self.past_state = 'BLOC'
        elif self.current_state == 'STRING' and self.past_state == 'BLOC':
            self.current_state = 'STRING'
            self.buffer =''
            self.current_space = 0
            self.tab = 0
        elif self.current_state == 'STRING' or self.current_state == 'CLE':
            self.past_state= self.current_state
            self.current_state = 'DEBUT'
            self.buffer = ''
            self.current_space = 0
            self.tab = 0

        elif self.current_state == 'COLON':
            self.current_state = 'TABLEAU'
            self.tab = 0
            self.current_space  = 0
            self.buffer= ''
            self.expected_tab +=1
        elif self.current_state =='DEBUT':
            self.current_space = 0
            self.tab = 0
            self.expected_tab = 0 if self.expected_tab == 0 else self.expected_tab -1
            return True
        else :
            return False
        return True
# Nouveau document (---)
    def handle_document_start(self):
        if self.current_state not in ['DEBUT', 'FIN_DOC']:
            print('Début de document inattendu.')
            return False
        # si présence des trois tirets on commence un nouveau document
        print('Nouveau document détecté.')
        self.reset_state_for_new_document()
        return True

# Fin de document (...)
    def handle_document_end(self):
        if self.current_state not in ['DEBUT', 'FIN_DOC']:
            print('Fin de document inattendue.')
            return False
        # si présence des trois points on termine un document
        print('Fin de document détectée.')
        self.current_state = 'FIN_DOC'
        return True
# Réinitialisation des états pour un nouveau document
    def reset_state_for_new_document(self):
        self.current_state = 'DEBUT'
        self.past_state = 'DEBUT'
        self.buffer = ''
        self.current_space = 0
        self.tab = 0
        self.expected_tab = 0      
# Nouvel espace ( )
    def handle_space(self):
        # en debut de ligne, on gère l'indentation
        if self.current_state =='DEBUT' :
            self.current_space += 1
            if self.current_space % 2==0 :
                self.tab += 1
            return True
        # si on vient de rencontrer un deux points, on a le droit d'avoir un espace
        elif self.current_state == 'COLON':
            return True
        # si l'on se trovue dans un tableau et que le buffer est vide, ce que nous sommes sur une nouvelle ligne donc une indentation est attendue
        elif self.current_state == 'TABLEAU' and not self.buffer:
            self.current_space += 1
            if self.current_space % 2==0 :
                self.tab += 1
                return True
            return True
        elif self.current_state == 'CLE' and self.past_state == 'TABLEAU':
            self.current_state = 'STRING'
        # si l'on se trouve dans un bloc et que le buffer est vide, cela signifie que nous sommes sur une nouvelle ligne donc une indentation est attendue, sinon on est en milieu de phrase
        elif self.current_state == 'STRING' and self.past_state == 'BLOC':
            if self.buffer=='':
                self.current_space += 1
                if self.current_space % 2==0 :
                    self.tab += 1
                    return True
            else: 
                self.buffer += ' '
            return True
        elif self.current_state in ['STRING' ,'COMMENTAIRE','LISTE']:
            self.buffer += ' '
            return True
        else :
            print('Espace inattendu')
            return False  
        
# Nouveau deux points (:)
    def handle_colon(self):
        if self.current_state == 'CLE':
            self.current_state = 'COLON'
            self.buffer = ''
            return True
        else:
            print('Mauvaise utilisation des deux points')
            return False
# Nouveau caractère alphanumérique et autres
    def handle_scalar_char(self, char):
        if self.current_state == 'DEBUT':
            if self.tab <= self.expected_tab:
                self.current_state = 'CLE'
                self.buffer += char 
                self.array_indent = None
                return True
            else:
                return False
        elif self.current_state == 'CLE':
            if self.tab <= self.expected_tab:
                self.buffer += char 
                return True
            else: 
                print('Erreur d\'indentation')
                return False
        elif self.current_state == 'TABLEAU' and self.expected_tab == self.tab:
            self.current_state = 'CLE'
            self.buffer += char
            self.past_state = 'TABLEAU'
        elif self.current_state == 'LISTE':
            self.current_state = 'CLE'
            self.past_state = 'LISTE'
            self.buffer += char
        elif self.current_state =='STRING' and self.past_state == 'BLOC':
            if self.tab == self.expected_tab:
                self.buffer += char
            elif self.tab < self.expected_tab: # sortie du bloc
                self.current_state = 'CLE'
                self.past_state = 'STRING'
                self.buffer += char
                self.expected_tab = self.tab
        else: 
            self.buffer += char
            self.current_state = 'STRING'
        
        return True
# Nouveau commentaire (#)
    def handle_comment_start(self):
        self.current_state = 'COMMENTAIRE'
        return True
# Nouveau tiret (-)
    def handle_dash(self):
        if self.current_state== 'TABLEAU':
            self.current_state = 'LISTE'
            self.buffer = ''
            self.array_indent = self.tab
            self.tab += 1
            self.expected_tab = self.tab
        elif self.array_indent is not None and self.tab == self.array_indent:
            self.current_state = 'LISTE'
            self.buffer = ''
        elif self.current_state == 'CLE' or self.current_state == 'STRING':
            self.buffer += '-'
        elif self.current_state == 'DEBUT' and self.tab == self.expected_tab -1  and self.inlist:
            self.current_state = 'LISTE'
            self.buffer = ''
        elif self.current_state =='DEBUT' and self.tab == self.expected_tab:
            self.current_state = 'LISTE'
            self.inlist = True
            self.buffer = ''
            self.expected_tab += 1
        else :
            print('Tiret inattendu')
            return False
        return True
# Nouveau point (.)
    def handle_dot(self):
        if self.current_state == 'STRING':
            self.buffer += '.'
        else: 
            print('Point inattendu')
            return False
        return True
# Nouveau bloc (| ou >)
    def handle_bloc(self):
        if self.tab == self.expected_tab:
            if self.current_state in ['STRING', 'CLE', 'COLON']:
                self.current_state = 'BLOC'
                self.expected_tab = self.tab+1
                return True
            else:
                print('Bloc inattendu')
                return False
        else:
            print('Erreur d\'indentation')
            return False
# Nouvelle ancre (&)
    def handle_anchor_definition(self, file):
        if self.current_state == 'STRING':
            self.buffer += '&'
        elif self.current_state== 'COLON':
            anchor_name = ''
            while (char := file.read(1)) and char not in ('\n'):
                if char == ' ':
                    print('Espace inattendu dans le nom de l\'ancre.')
                    return False
                else:
                    anchor_name += char
            self.anchors.append(anchor_name)
            self.current_state = 'DEBUT'
            return True
        else:
            print('Esperluette inattendue')
            return False
        return True
# Nouvelle référence d'ancre (*)
    def handle_anchor_reference(self, file):
        if self.current_state == 'STRING':
            self.buffer += '*'
        elif self.current_state == 'COLON':
            anchor_name = ''
            while (char := file.read(1)) and char not in (' ', '\n'):
                anchor_name += char
            if anchor_name not in self.anchors:
                print('Ancre non définie.')
                return False
            self.current_state = 'DEBUT'
            return True
        else:
            print('Astérisque inattendu')
            return False
        return True
# Aide de test pour gérer les erreurs    
    def print_state(self, char):
        print(f'{char} | current_state: {self.current_state} | past_state: {self.past_state} | buffer: {self.buffer} | current_space: {self.current_space} | tab: {self.tab} | expected_tab: {self.expected_tab} | anchors: {self.anchors}')

# Parcours du fichier
    def parse_file(self, filepath):
        with open(filepath, 'r') as file:
            while (char := file.read(1)):
                self.print_state(char)
                if not self.process_char(char,file):
                    print('Caractère non reconnu ou incorrect:', char)
                    return False  
            if self.buffer:
                if not self.handle_newline():
                    print('Buffer non vide en fin de fichier.')
                    return False
            if self.current_state not in ['DEBUT', 'FIN_DOC']:
                print('Document final terminé implicitement.') 
        return True  # Si le fichier est parsé sans erreur
# Appel de la fonction    
yaml_parser = YamlParser()
result = yaml_parser.parse_file('file4.yaml') # Entrer le chemin du fichier à tester
print('Le fichier est valide YAML.' if result else 'Le fichier n\'est pas valide YAML.')