
class YamlParser:
    def __init__(self):
        # États possibles
        self.states = ['DEBUT', 'CLE', 'LISTE', 'COMMENTAIRE', 'SCALAIRE', 'FIN', 'FIN_DOC', 'BLOC_LIGNE', 'BLOC_ANCRE']
        self.current_state = 'DEBUT'
        self.indent_stack = []  # Pile pour gérer l'indentation
        self.current_indent = 0 # Pour suivre la ligne courante et l'indentation
        self.buffer = ""  # Pour stocker les tokens temporaires
        self.anchors = [] # Pour stocker les ancres
        self.dash_count = 0

    def process_char(self, char, file):
        # Gestion des états selon le caractère
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
        # Fin d'une ligne, analyser le buffer et réinitialiser pour la prochaine ligne
        if self.current_state == 'COMMENTAIRE':
            pass  # Pas d'action particulière pour le commentaire
        elif self.current_state == 'CLE':
            if not self.buffer:  # Erreur si la clé est vide
                print("current_state", self.current_state)
                print("Erreur: La clé ne peut pas être vide.")
                return False
        elif self.current_state == 'LISTE':
            if not self.buffer:  # Erreur si l'élément de liste est vide
                print("current_state", self.current_state)
                print("Erreur: L'élément de liste ne peut pas être vide.")
                return False
        elif self.current_state == 'SCALAIRE':
            if not self.buffer:  # Erreur si le scalaire est vide
                print("current_state", self.current_state)
                print("Erreur: Le scalaire ne peut pas être vide.")
                return False

        # Réinitialiser le buffer et retourner à un état de base
        self.buffer = ""
        self.current_state = 'DEBUT'
        self.current_indent = 0
        return True

    def handle_space(self):
        # Compter les espaces pour gérer l'indentation
        if self.current_state == 'DEBUT':
            self.current_indent += 1
        elif self.current_state == 'CLE':
            self.current_state = 'SCALAIRE'
            self.buffer += ' '  # Ajouter l'espace au buffer dans d'autres cas
        return True

    def handle_comment_start(self):
        if self.current_state == 'DEBUT':
            self.current_state = 'COMMENTAIRE'
        return True

    def handle_colon(self):
        if self.current_state == 'CLE':
            self.current_state = 'SCALAIRE'
        else:
            print("current_state", self.current_state)
            print("Erreur: ':' ne peut pas être utilisé dans ce contexte.")
            return False  # Erreur si le ':' apparaît dans un contexte inattendu
        return True

    def handle_dash(self):
        if self.current_state == 'DEBUT':
            self.dash_count += 1
            if self.dash_count == 3:  # Si trois tirets consécutifs sont détectés
                self.dash_count = 0  # Réinitialiser le compteur
            return True
        elif self.current_state == 'DEBUT':
            self.current_state = 'LISTE'
        elif self.current_state == 'LISTE':
            return True
        elif self.current_state == 'SCALAIRE':
            self.buffer += '-'
        else:
            print("current_state", self.current_state)
            print("Erreur: '-' ne peut pas être utilisé dans ce contexte.")
            return False  # Erreur si '-' apparaît dans un contexte inattendu
        return True
    
    def handle_dot(self):
        # Gestion des trois points pour la fin de document
        if self.current_state == 'DEBUT' or self.current_state == 'FIN_DOC':
            self.buffer += '.'
            if self.buffer == '...':
                self.current_state = 'FIN_DOC'  # Indique la fin du document
                return True
            elif len(self.buffer) > 3:
                print("current_state", self.current_state)
                print("Erreur: Les trois points ne peuvent pas être utilisés dans ce contexte.")
                return False  # Erreur si plus de trois points sont présents
        elif self.current_state == 'SCALAIRE':
            self.buffer += '.'
        else:
            print("current_state", self.current_state)
            print("Erreur: Les trois points ne peuvent pas être utilisés dans ce contexte.")
            return False  # Erreur si des points apparaissent dans un contexte inattendu
        return True
    def handle_bloc(self):
        # Bloc multi-lignes
        if self.current_state == 'DEBUT'or self.current_state == 'CLE' :
            self.current_state = 'BLOC_LIGNE'
        else:
            print("current_state", self.current_state)
            print("Erreur: '|' ou '>' ne peuvent pas être utilisés dans ce contexte.")
            return False
        return True

    def handle_anchor_definition(self, file):
        # Gestion de la définition d'une ancre avec `&`
        # if self.current_state == 'DEBUT' or self.current_state == 'CLE':
        #     self.current_state = 'BLOC_ANCRE'
        # else:
        #     print("current_state", self.current_state)
        #     print("Erreur: '&' ne peut pas être utilisé dans ce contexte.")
        #     return False
        # return True
        if self.current_state in ['DEBUT', 'CLE']:
            self.current_state = 'BLOC_ANCRE'
            anchor_name = ""
            
            # Lire jusqu'à ce qu'on rencontre un espace ou un caractère de fin de ligne pour capturer l'ancre
            while True:
                char = file.read(1)
                if char in (' ', '\n') or not char:
                    break
                anchor_name += char
            
            self.anchors.append(anchor_name)
            
            self.buffer = ""  # Réinitialiser le buffer
            return True
        else:
            print(f"Erreur: '&' ne peut pas être utilisé dans le contexte '{self.current_state}'.")
            return False

    def handle_anchor_reference(self, file):
        # Gestion de la référence d'une ancre avec `*`
        # if self.current_state == 'DEBUT' or self.current_state == 'CLE':
        #     if self.buffer in self.anchors:
        #         self.current_state = 'SCALAIRE'
        #     else:
        #         print("current_state", self.current_state)
        #         print(f"Erreur: L'ancre {self.buffer} n'est pas définie.")
        #         return False
        # else:
        #     print("current_state", self.current_state)
        #     print("Erreur: '*' ne peut pas être utilisé dans ce contexte.")
        #     return False
        # return True
        if self.current_state in ['DEBUT', 'CLE']:
            anchor_name = ""

            # Lire jusqu'à rencontrer un espace ou un caractère de fin de ligne pour capturer la référence
            while True:
                char = file.read(1)
                if char in (' ', '\n') or not char:
                    break
                anchor_name += char
            
            if anchor_name in self.anchors:
                print(f"Ancre trouvée: {anchor_name}")
                return True
            else:
                print(f"Erreur: L'ancre '{anchor_name}' n'est pas définie.")
                return False
        else:
            print(f"Erreur: '*' ne peut pas être utilisé dans le contexte '{self.current_state}'.")
            return False

    def handle_scalar_char(self, char):
        if self.current_state in ['DEBUT', 'CLE', 'LISTE', 'SCALAIRE', 'BLOC_LIGNE', 'BLOC_ANCRE']:
            self.current_state = 'SCALAIRE'
        self.buffer += char
        return True
    
    def parse_file(self, filepath):
        with open(filepath, 'r') as file:
            while (char := file.read(1)):
                if not self.process_char(char, file):
                    print("buffer", self.buffer)
                    return False  # Retourne False si une erreur de syntaxe est détectée
            # Une fois la boucle terminée, gérer la fin du fichier
            if self.buffer:  # Si un token reste à la fin du fichier
                if not self.handle_newline():
                    return False
        return True  # Si le fichier est parsé sans erreur

# Exemple d'utilisation
yaml_parser = YamlParser()
result = yaml_parser.parse_file('file2.yaml')
print("Le fichier est valide YAML:" if result else "Le fichier n'est pas valide YAML.")


# verif 4 , 5 (passe alors que dervait pas ), 6 (idem), 7 ( ! apres * ou & pas de texte directe \n), 8