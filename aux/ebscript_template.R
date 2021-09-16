source("inferencefunctions.R")
genodat <- read.table("GENOTYPES",as.is=T)
ancestryprops <- read.table("ANCESTRYPROPS",as.is=T)
allelicdropoutrates = t(read.table("DROPOUT",as.is=T))
nmarkers = ncol(allelicdropoutrates)
ancestrythreshold =0.95
errorprob = 0
lls = getloglikes(genodat,nmarkers,ancestryprops,ancestrythreshold,errorprob,allelicdropoutrates)
hybt = getallposteriors(lls)
HPs=gethybridposteriors(hybt)
writeResults2files("SGP_hybt",hybt$posteriors)
writeResults2files("SGP_HPs",HPs)
