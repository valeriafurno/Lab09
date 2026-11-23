from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self._escursioni_parco = []

        #vincoli
        self._max_giorni = None
        self._max_budget = None

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO
        #recupero tutte le relazioni dal DAO
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()

        for relazione in relazioni:
            id_escursione = relazione["id_escursione"]
            id_punto = relazione["id_punto_interesse"]

            #recupero gli oggetti dai dizionari
            escursione = self.escursioni_map[id_escursione]
            punto = self.punti_interesse_map[id_punto]

            #il collegamento è bidirezionale, quindi aggiungo il punto all'escursione e l'escursione al punto
            escursione.punti_interesse.add(punto)
            punto.escursioni.add(escursione)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        #seleziono solo le escursioni del parco scelto
        self._escursioni_parco = []
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                self._escursioni_parco.append(escursione)

        self._ricorsione(0,[], 0, 0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        for i in range(start_index, len(self._escursioni_parco)):
            escursione = self._escursioni_parco[i]

            #CONTROLLO SUI VINCOLI
            #verifica sui punti di interesse uguali, non devono esserci duplicati
            if punti_usati.intersection(escursione.punti_interesse): #intersection: restituisce gli elementi che sono presenti in entrambi gli insiemi
                continue
            #veriica sulla durata complessiva; non deve superare il limite
            if self._max_giorni is not None and durata_corrente + escursione.durata_giorni > self._max_giorni:
                continue
            #verifica sul budget
            if self._max_budget is not None and costo_corrente + escursione.costo > self._max_budget:
                continue

            pacchetto_parziale.append(escursione)

            durata_corrente += escursione.durata_giorni
            costo_corrente += escursione.costo

            punti_usati.update(escursione.punti_interesse)

            #calcolare il valore dei punti di interesse dell'escursione
            valore_escursione = 0
            for punto in escursione.punti_interesse:
                valore_escursione += punto.voto_visitatori
            valore_corrente += valore_escursione

            self._ricorsione(i+1, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, punti_usati)

            #BACKTRACKING
            pacchetto_parziale.pop()
            durata_corrente -= escursione.durata_giorni
            costo_corrente -= escursione.costo
            valore_corrente -= valore_escursione

            punti_usati.difference_update(escursione.punti_interesse) #difference_update() rimuove da un insieme tutti gli elementi che sono presenti in un altro insieme