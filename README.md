# 🔄 HSRP — Haute Disponibilité sur Matériel Cisco Réel

![Cisco](https://img.shields.io/badge/Cisco_IOS-Routeurs_Physiques-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white)
![HSRP](https://img.shields.io/badge/HSRP-Hot_Standby_Router_Protocol-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![BTS SIO](https://img.shields.io/badge/BTS_SIO-IRIS_Paris-blueviolet?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen?style=for-the-badge)

---

## 📋 Description

TP réalisé sur **matériel physique Cisco** (deux routeurs réels) dans le cadre du **BTS SIO à IRIS Paris**.  
Configuration du protocole **HSRP (Hot Standby Router Protocol)** pour assurer la haute disponibilité de la passerelle réseau.  
Validation du basculement automatique (failover) entre le routeur actif et le routeur de secours via un script Python.

---

## 🏗️ Topologie réseau

```
                        [Réseau LAN 192.168.1.0/24]
                                   |
              ┌────────────────────┴────────────────────┐
              │                                         │
       ┌──────┴──────┐                         ┌───────┴──────┐
       │   R1 (Active) │                         │ R2 (Standby) │
       │  192.168.1.1  │                         │  192.168.1.2 │
       │  Priorité 110 │                         │  Priorité 100│
       └──────┬──────┘                         └───────┬──────┘
              └────────────────────┬────────────────────┘
                                   │
                          IP Virtuelle HSRP
                           192.168.1.254
                        (Gateway des clients)
```

| Équipement | Rôle HSRP | IP Interface | Priorité | Préemption |
|---|---|---|---|---|
| **R1** | Active (Principal) | 192.168.1.1 | 110 | Activée |
| **R2** | Standby (Secours) | 192.168.1.2 | 100 | Désactivée |
| **VIP** | IP Virtuelle | 192.168.1.254 | — | — |

---

## ⚙️ Configuration Cisco IOS

### R1 — Routeur Actif (Active)

```cisco
! ============================================
! R1 — Configuration HSRP (Routeur Actif)
! ============================================
hostname R1

interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown

 ! Configuration HSRP groupe 1
 standby 1 ip 192.168.1.254        ! IP virtuelle partagée
 standby 1 priority 110            ! Priorité haute → devient Active
 standby 1 preempt                 ! Reprend le rôle Active si disponible
 standby 1 timers 1 3              ! Hello 1s / Dead 3s
 standby 1 track GigabitEthernet0/1 10  ! Réduit priorité si lien WAN down

end
```

### R2 — Routeur Standby (Secours)

```cisco
! ============================================
! R2 — Configuration HSRP (Routeur Standby)
! ============================================
hostname R2

interface GigabitEthernet0/0
 ip address 192.168.1.2 255.255.255.0
 no shutdown

 ! Configuration HSRP groupe 1
 standby 1 ip 192.168.1.254        ! Même IP virtuelle
 standby 1 priority 100            ! Priorité basse → reste Standby
 standby 1 timers 1 3              ! Hello 1s / Dead 3s

end
```

---

## 🗂️ Structure du projet

```
📦 hsrp-haute-disponibilite/
├── 📄 README.md                  ← Ce fichier
├── 🐍 test_hsrp.py               ← Script Python de validation failover
├── 📄 R1_active.txt              ← Config complète IOS R1
├── 📄 R2_standby.txt             ← Config complète IOS R2
└── 📄 .gitignore
```

---

## 🐍 Script de validation Python

Le script `test_hsrp.py` vérifie automatiquement le basculement HSRP :

- ✅ Ping continu vers l'IP virtuelle `192.168.1.254`
- ✅ Détection de la perte de connectivité lors du failover
- ✅ Mesure du temps de basculement (< 3 secondes avec timers 1/3)
- ✅ Confirmation de la reprise par R2 (Standby → Active)

```bash
# Exécution du script de test
python3 test_hsrp.py --target 192.168.1.254 --duration 60
```

---

## ✅ Résultats obtenus

| Test | Résultat | Détail |
|---|---|---|
| **Élection HSRP** | ✅ OK | R1 élu Active (priorité 110 > 100) |
| **IP virtuelle accessible** | ✅ OK | Ping 192.168.1.254 réussi |
| **Failover R1 → R2** | ✅ OK | Basculement en < 3 secondes |
| **Reprise R1 (preempt)** | ✅ OK | R1 reprend le rôle Active |
| **Temps de coupure** | ✅ ~2s | Mesuré via script Python |

---

## 🔍 Commandes de vérification IOS

```cisco
! Vérifier l'état HSRP
show standby
show standby brief

! Exemple de sortie attendue sur R1
! GigabitEthernet0/0 - Group 1
!   State is Active
!   Active virtual IP address is 192.168.1.254
!   Active router is local
!   Standby router is 192.168.1.2, priority 100
!   Priority 110 (configured 110)
!   Preemption enabled
```

---

## 📚 Concepts clés

**HSRP (Hot Standby Router Protocol)** est un protocole propriétaire Cisco (RFC 2281) qui permet :
- La **redondance de passerelle** — une seule IP virtuelle pour les clients
- Le **basculement automatique** — si le routeur actif tombe, le standby prend le relais
- La **préemption** — le routeur prioritaire reprend son rôle dès qu'il revient en ligne

**États HSRP :** Initial → Learn → Listen → Speak → **Standby** → **Active**

---

## 🛠️ Environnement technique

| Élément | Détail |
|---|---|
| **Matériel** | 2 routeurs Cisco physiques (IOS 15.x) |
| **Protocole** | HSRP v1 (groupe 1) |
| **Réseau LAN** | 192.168.1.0/24 |
| **IP Virtuelle** | 192.168.1.254 |
| **Timers** | Hello 1s / Dead 3s |
| **Script test** | Python 3.x |
| **Établissement** | IRIS Paris — BTS SIO |

---

## 👤 Auteur

| Champ | Information |
|---|---|
| **Nom** | Julien Lesnichenko |
| **Formation** | BTS SIO — IRIS Paris |
| **Année** | 2024 - 2025 |
| **GitHub** | [@JLko-cyber](https://github.com/JLko-cyber) |

---

## 🏷️ Tags

`hsrp` `cisco` `networking` `haute-disponibilite` `bts-sio` `python` `cisco-ios` `failover` `gateway-redundancy` `iris-paris`
