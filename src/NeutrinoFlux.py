from math import *
import numpy as np
import sys
import scipy.integrate as integrate
import os

# ============================================================================
# MAIN ARTICLE
# ============================================================================
# Ebe04: 
#   Eberle 2004
#   Relic Neutrino Absorption Spectroscopy
#   arxiv:hep-ph/0401203
# ============================================================================
# OTHER ARTICLES referred to in comments:
# ============================================================================
# Aar15:
#   Aartsen, 2015
#   Atmospheric and Astrophysical Neutrinos above 1 TeV Interacting in IceCube
#   arXiv:1410.1749v2
# Ahl14:
#   Ahlers, 2014
#   Pinpointing extragalactic neutrino sources in light of recent IceCube 
#       observations
#   arXiv: 1406.2160v1
# Bau17:
#   Baumann, 2017
#   Syllabus Cosmology course UvA 2017
#   http://www.damtp.cam.ac.uk/user/db275/Cosmology/Lectures.pdf
# Fan16:
#   Fang, 2016
#   High-energy neutrinos from sources in clusters of galaxies
#   arXiv:1607.00380
# Fod03:
#   Fodor, 2003
#   Bounds on the cosmogenic neutrino flux
#   arXiv:hep-ph/0309171v1
# Oli06:
#   D'Olivo, 2006
#   UHE neutrino damping in a thermal gas of relic neutrinos
#   arXiv:astro-ph/0507333v2
# Lun13:
#   Lunardini 2013
#   Ultra High Energy Neutrinos: Absorption, Thermal Effects and Signatures
#   arXiv:1306.1808v2
# Wic04:
#   Wick, 2004
#   High-energy cosmic rays from gamma-ray bursts
#   arXiv:astro-ph/0310667v2
# ============================================================================

class NeutrinoFlux():
    def __init__(self):
        self.z_min = 0
        self.z_max = 20.
        self.alpha = 1.
        self.n = 1.
        self.m_n = 1.
        self.eta0 = 1e-5 # [Mpc^-3]
        self.j = 3e6
        self.Z_decay = True
        self.FluxEalpha = True
        if self.m_n >0:
            self.E_resonance()
        self.Emin = 0.
        self.Emax = 5e22

    def E_resonance(self):
        ''' Function to determine the resonance energy [eV] 
        for given neutrino mass [eV]'''
        assert(self.m_n >0), "Neutrino massless"
        m_z = 91.2e9    # [eV]
        self.Eres = m_z**2 / (2. * self.m_n)                                   # (eq 1)

    def Hubble(self, z, h=0.678, Om=0.308, Ol=0.692, Ok=0.):
        '''Function to determine the hubble parameter at given z. The curvature 
        parameters are given a default values resulting in a flat universe'''
        # default values from Ebe04
        H0 = 100 * h
        # 100 h [km/s/Mpc]
        # <== NOG KEER EEN CONSTANTE VOOR DIMENSIONS, however,
        # J and eta0 in source emisivity also unknown --> doesn't matter
        return sqrt(H0**2 * ( Om * (1+z)**3 + Ok * (1+z)**2 + Ol) )                 # (eq 8)

    def Ebe04_survival_probability_P(self, e, z, 
                                     h=0.678, Om=0.308, Ol=0.692, Ok=0.):
        '''Funtion that returns survival probability for the e values 
        within range: Eres/(1+z) < e < Eres ''' 

        ann_prob = 0.678/h * 0.03        # anihilation probability                   # (Ebe04: eq16)
        assert(float(Om + Ol + Ok) == 1.), "No Flat Universe!"

        if e < self.Eres/(1+z) or e > self.Eres:
            return 1.                   # No absorption
        else:
            return exp(-ann_prob * (((self.Eres/e)**3) / sqrt(Om*((self.Eres/e)**3) 
                   + Ok*((self.Eres/e)**2) + Ol)))                                              # (eq15)


    def Ebe04_source_emissivity_L_z(self, z):
        # Wic04: explaines powerlaw ansatz. NB: approximation is appropriate
        # upto z ~ 2, but for E_{CR} < 10^18 eV -->  predicting too high flux
        '''Function that returns all parts of the source emissivity function that DO depend on z'''
        n_min_alpha = self.n - self.alpha
        if z > self.z_min:
            if z < self.z_max:
                return (1 + z) ** n_min_alpha
            # (eq 24 --> eq 27&28, but only z-dependent part (for integration))
            else:
                return 0.
        return 0.

    def Ebe04_source_emissivity_L_no_z(self, e):
        # VERY UNCERTAIN!
        '''Function that returns all parts of the source emissivity function that DO NOT depend on z'''

        # (eq 24 --> eq 27&28, but only z-independent part)
        return self.eta0 * self.j * e**(-self.alpha)                                               

    def Ebe04_neutrino_flux_earth_F(self, e, absorption=True): 
        '''Function to determine the Flux per neutrino flavor by integrating 
        the survival probability * source emissivity / Hubble parameter
        over all redshifts z and multiply it by some constants.
        When no absorption is included the survival probabiliy is set to 1'''

        if absorption == True:
            # - function to integrate for Flux
            f1_to_integrate = lambda z: 1/self.Hubble(z) * \
                              self.Ebe04_survival_probability_P(e, z) * \
                              self.Ebe04_source_emissivity_L_z(z)
        elif absorption == False:
            # - function to integrate for Flux without absorption
            f1_to_integrate = lambda z: 1/self.Hubble(z) * \
                              self.Ebe04_source_emissivity_L_z(z)

        # INTEGRATION BOUNDARIES:
        integrant1, err1 = integrate.quad(f1_to_integrate, self.z_min, self.z_max)

        # if z > z_max; L (Ebe04_source_emissivity_L_z) returns 0, therfore this doesn't add anything to the integral
        # Lun13: for E > 10^11 GeV, neutrinio horizon of z ~ 140,
        # beyond which universe is opaque to neutrinos <= taking this as upperlimit gives the same
        # Bau17: neutrino decoupling at redshift z = 6e9 <= taking this as upperlimit goes wrong... ?
        # Ebe04: in eq 23 an integral to np.inf is shown.
        # But this gives the same result as z=z_max, and z=140 since z>z_max doesn't add anything

        return 1/(4 * pi) * integrant1 * 1/3. * self.Ebe04_source_emissivity_L_no_z(e)


    def Ebe05_neutrino_flux_earth_F(self, e, absorption=True):
        '''Function to determine the Flux per neutrino flavor with the option to
        include primary flux only (Z_decay = False),
        or include primary flux as well as secondary flux (Z_decay = True)'''
        
        primary_flux = self.Ebe04_neutrino_flux_earth_F(e, absorption)
        
        if absorption == False:
            # if no absorption; no UHE Z-boson created, so no secondary neutrinos
            return primary_flux                                                 # <== eigenlijk nog keer 3 ivm 3 Neutrino spicies, maar y-as is toch arbitrary
        
        if self.Z_decay == False:
            return primary_flux

        elif self.Z_decay == True:
            # Z -> nu nu in 20% of the decaying processes. here times 2 since doubling of neutrino detection possibility
            decay_frac_to_nu = 0.4
            secondary_flux = self.Ebe04_neutrino_flux_earth_F(2*e, absorption=False) - \
                             self.Ebe04_neutrino_flux_earth_F(2*e, absorption=True)
            return primary_flux + secondary_flux * decay_frac_to_nu


    def save_to_ascii(self, prefix):
        E = np.linspace(self.E_min, self.E_max, 10000)                                      # <= RANGE config dep!

        savename = prefix + "_H0H1_m%s_zmax%i_n%i_alpha%i_Zdecay%s.txt" \
                     %(self.m_n , self.z_max, self.n, self.alpha, self.Z_decay)

#        if savename in  os.listdir(os.curdir):
#            print "Do you want to overwrite the file \n - %s" %(savename)
#            var = raw_input("Please enter Y or N: ")
#            while var != 'Y' and var != 'N':
#                print "###\nUnknown input, please try again:"
#                print "Do you want to overwrite the file \n - %s" %(savename)
#                var = raw_input("Please enter Y or N: ")
#            if var == 'N':
#                sys.exit()

        # H0 data: there is NO dip in the spectrum
        print "Writing data to txt file for absorption (H1), and no absorption (H0). \nOne moment please..."
        with open(savename, 'w') as f:
            if self.FluxEalpha == True:
                for e in E:
                    H0FluxE2 = self.Ebe05_neutrino_flux_earth_F(e, absorption = False) * (e**self.alpha)
                    H1FluxE2 = self.Ebe05_neutrino_flux_earth_F(e, absorption = True) * (e**self.alpha)
                    line = "%s\t%s\t%s\n" %(e, H0FluxE2, H1FluxE2)
                    f.write(line)
            else:
                for e in E:
                    H0FluxE2 = self.Ebe05_neutrino_flux_earth_F(e, absorption = False)
                    H1FluxE2 = self.Ebe05_neutrino_flux_earth_F(e, absorption = True)
                    line = "%s\t%s\t%s\n" %(e, H0FluxE2, H1FluxE2)
                    f.write(line)

