class YamlParser:
    def __init__(self):
        self.states = [ 'DEBUT', 'CLE','TABLEAU', 'LISTE', 'COMMENTAIRE', 'STRING', 'BLOC',"FIN_DOC"]
        self.current_state = 'DEBUT'
        self.past_state = 'DEBUT'
        self.buffer = ""
        self.current_indent = 0
        self.tab = 0
        self.expected_tab = 0
        self.anchors = []
        
    def process_char(self, char, file):
    # Gestion des états selon le caractère
        if self.current_state == 'DEBUT' and char in ('-', '.') and self.current_indent==0 and self.expected_tab == 0:
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
                print("Séquence non reconnue.")
                return False
            return True
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
        
    def handle_newline(self):
        if self.current_state == "BLOC":
            self.current_indent = 0
            self.tab = 0
            self.current_state="STRING"
            self.past_state = "BLOC"
        elif self.current_state == 'STRING' and self.past_state == 'BLOC':
            self.current_state = 'STRING'
            self.buffer =""
            self.current_indent = 0
            self.tab = 0
        elif self.current_state == 'STRING':
            self.buffer = ''
            self.current_indent = 0
            self.current_state = 'DEBUT'
            self.tab =0
        elif self.current_state == 'COLON':
            self.current_state = 'TABLEAU'
            self.buffer= ''
            self.expected_tab +=1
        elif self.current_state == 'CLE':
            self.current_state = 'DEBUT'
            self.buffer = ''
            self.current_indent = 0
            self.tab = 0
        elif self.current_state =='DEBUT':
            self.current_indent = 0
            self.tab = 0
            self.expected_tab = 0 if self.expected_tab == 0 else self.expected_tab -1
            return True
        else :
            return False
        return True

    def handle_document_start(self):
        if self.current_state not in ['DEBUT', 'FIN_DOC']:
            print("Début de document inattendu.")
            return False

        print("Nouveau document détecté.")
        self.reset_state_for_new_document()
        return True

    def handle_document_end(self):
        if self.current_state not in ['DEBUT', 'FIN_DOC']:
            print("Fin de document inattendue.")
            return False

        print("Fin de document détectée.")
        self.current_state = 'FIN_DOC'
        return True
    
    def reset_state_for_new_document(self):
        self.current_state = 'DEBUT'
        self.past_state = 'DEBUT'
        self.buffer = ""
        self.current_indent = 0
        self.tab = 0
        self.expected_tab = 0      
        
    def handle_space(self):
        if self.current_state =="DEBUT" :
            self.current_indent += 1
            if self.current_indent % 2==0 :
                self.tab += 1
            return True
        elif self.current_state == 'COLON':
            return True
        elif self.current_state == 'TABLEAU' and not self.buffer:
            self.current_indent += 1
            if self.current_indent % 2==0 :
                self.tab += 1
                return True
            return True
        elif self.current_state == 'CLE' and self.past_state == 'TABLEAU':
            self.current_state = 'STRING'
        elif self.current_state == "STRING" and self.past_state == 'BLOC':
            if self.buffer=="":
                self.current_indent += 1
                if self.current_indent % 2==0 :
                    self.tab += 1
                    return True
            else: 
                self.buffer += ' '
            return True
        elif self.current_state in ["STRING" ,"COMMENTAIRE","LISTE"]:
            self.buffer += ' '
            return True
        else :
            print("space error")
            return False  
        
    
    def handle_colon(self):
        if self.current_state == 'CLE':
            self.current_state = 'COLON'
            self.buffer = ""
            return True
        else:
            print("colon error")
            return False
        
    def handle_scalar_char(self, char):
        if self.current_state == 'DEBUT' or self.current_state == 'CLE':
            if self.tab <= self.expected_tab:
                self.current_state = 'CLE'
                self.buffer += char 
                return True
            else: 
                return False
        elif self.current_state == 'TABLEAU' and self.expected_tab == self.tab:
            self.current_state = 'CLE'
            self.buffer += char
            self.past_state = 'TABLEAU'
        elif self.current_state == 'LISTE':
            self.current_state = 'CLE'
            self.buffer += char
        elif self.current_state =='STRING' and self.past_state == 'BLOC':
            if self.tab == self.expected_tab:
                self.buffer += char
            elif self.tab < self.expected_tab:
                self.current_state = 'CLE'
                self.past_state = 'STRING'
                self.buffer += char
                self.expected_tab = self.tab
        else: 
            self.buffer += char
            self.current_state = 'STRING'
        
        return True
    
    def handle_comment_start(self):
        self.current_state = 'COMMENTAIRE'
        return True
    def handle_dash(self):
        if self.current_state== 'TABLEAU':
            self.current_state = 'LISTE'
            self.buffer = ""
        elif self.current_state == "CLE" or self.current_state == "STRING":
            self.buffer += '-'
        elif self.current_state =='DEBUT' and self.tab == self.expected_tab:
            self.current_state = 'LISTE'
            self.buffer = ""
            self.expected_tab += 1
        else :
            print("dash error")
            return False
        return True
    
    def handle_dot(self):
        if self.current_state == 'STRING':
            self.buffer += '.'
        else: 
            print("dot error")
            return False
        return True
    
    def handle_bloc(self):
        if self.tab == self.expected_tab:
            if self.current_state in ['STRING', 'CLE', 'COLON']:
                self.current_state = 'BLOC'
                self.expected_tab = self.tab+1
                return True
            else:
                print("bloc error")
                return False
        else:
            print("bloc error")
            return False

    def handle_anchor_definition(self, file):
        if self.current_state == 'STRING':
            self.buffer += '&'
        elif self.current_state== 'COLON':
            anchor_name = ""
            while (char := file.read(1)) and char not in ('\n'):
                if char == ' ':
                    print("anchor error no space")
                    return False
                else:
                    anchor_name += char
            self.anchors.append(anchor_name)
            self.current_state = 'DEBUT'
            return True
        else:
            print("anchor error")
            return False
        print("anchor", anchor_name)
        return True
    
    def handle_anchor_reference(self, file):
        if self.current_state == 'STRING':
            self.buffer += '*'
        elif self.current_state == 'COLON':
            anchor_name = ""
            while (char := file.read(1)) and char not in (' ', '\n'):
                anchor_name += char
            if anchor_name not in self.anchors:
                print(f"Erreur : ancre '{anchor_name}' non définie.")
                return False
            self.current_state = 'DEBUT'
            return True
        else:
            print("anchor error")
            return False
        return True
    



    def parse_file(self, filepath):
        with open(filepath, 'r') as file:
            while (char := file.read(1)):
                print(char)
                self.print_state()
                if not self.process_char(char,file):
                    return False  # Retourne False si une erreur de syntaxe est détectée
            if self.buffer:  # Si un token reste à la fin du fichier
                if not self.handle_newline():
                    return False
            if self.current_state not in ['DEBUT', 'FIN_DOC']:
                print("Document final terminé implicitement.") 
        return True  # Si le fichier est parsé sans erreur
    
    def print_state(self):
        print("current_state", self.current_state)
        print("past_state", self.past_state)
        print("buffer", self.buffer)
        print("current_indent", self.current_indent)
        print("tab", self.tab)
        print("expected_tab", self.expected_tab)
        print("anchors", self.anchors)
        print("\n")


yaml_parser = YamlParser()
result = yaml_parser.parse_file('file2.yaml')
print("Le fichier est valide YAML:" if result else "Le fichier n'est pas valide YAML.")



# probleme avec les listes
# commentaire du code
#erreur explicite
# Certaines méthodes, comme handle_space, pourraient être simplifiées en déléguant la logique à des sous-méthodes ou en consolidant les conditions similaires.
# Exemple : Réduire les cas où self.current_state est vérifié plusieurs fois en combinant les états similaires (STRING, COMMENTAIRE, etc.).
# mieux gerer les past state