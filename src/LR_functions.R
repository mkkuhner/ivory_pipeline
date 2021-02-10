###########################################
### functions to calculate pairwise LRs ###
###########################################

### set kinship kappas
UN_k <- c(1,0,0) # unrelated
DM_k <- c(0,0,1) # direct match
PO_k <- c(0,1,0) # parent-offspring
FS_k <- c(0.25, 0.5, 0.25) # full sibs
HS_k <- c(0.5, 0.5, 0) # half sibs

### calculates allele frequencies for a marker
calc_afs <- function(genotypes, allele_names){
  # drop -999 which corresponds to missing
  genotypes <- genotypes[!is.na(genotypes)]
  afs <- rep(NA, length(allele_names))
  for (i in 1:length(allele_names)){
    freq <- sum(genotypes == allele_names[i]) / length(genotypes)
    afs[i] <- freq
  }
  return(afs)
}

### calculates LR for specific relationship, takes 2x2 matrix of alleles
### we'll call the first row of the matrix G1, and the second row G2
calc_kinship <- function(unorder_gt_pair, kap, alleles, theta, afs){
  gt_pair <- matrix(NA, nrow=2, ncol=3)
  if (unorder_gt_pair[2,1] == unorder_gt_pair[2,2]){
    gt_pair[1,] <- unorder_gt_pair[2,]
    gt_pair[2,] <- unorder_gt_pair[1,]
  } else{
    gt_pair <- unorder_gt_pair
  }
  
  allele_name <- gt_pair[1,3]
  gt_pair <- gt_pair[,-3]
  
  gt_pair <- apply(gt_pair, 2, as.numeric)
  
  # get AFs from AF data frame
  p.a <- afs[which(alleles == gt_pair[1,1]),allele_name]
  p.b <- afs[which(alleles == gt_pair[1,2]),allele_name]
  p.c <- afs[which(alleles == gt_pair[2,1]),allele_name]
  p.d <- afs[which(alleles == gt_pair[2,2]),allele_name]
  
  # g1 homozygous
  if (gt_pair[1,1] == gt_pair[1,2]){
    # g1 = g2, both homozygous (CASE 1)
    if (sum(gt_pair[2,] == gt_pair[1,]) == 2){
      p_RE <- kap[1]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a)*(3*theta + (1-theta)*p.a) / 
              ((1+theta)*(1+2*theta))) + 
              kap[2]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a) / (1+theta)) + 
              kap[3]*(p.a*(theta + (1-theta)*p.a))
      p_UN <- UN_k[1]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a)*(3*theta + (1-theta)*p.a) / 
                         ((1+theta)*(1+2*theta))) + 
              UN_k[2]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a) / (1+theta)) + 
              UN_k[3]*(p.a*(theta + (1-theta)*p.a))
    } else if(gt_pair[2,1] == gt_pair[1,1] | 
              gt_pair[2,2] == gt_pair[1,1]){
    # one matching allele (CASE 3)
      # find which allele from gt2 matched the pair from gt1
      if (gt_pair[2,1] == gt_pair[1,1]){
        p.diff <- p.d
      } else{
        p.diff <- p.c
      }
      p_RE <- 2*kap[1]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a)*((1-theta)*p.diff) / 
                         ((1+theta)*(1+2*theta))) + 
              kap[2]*(p.a*(theta + (1-theta)*p.a)*((1-theta)*p.diff) / 
              (1+theta))
        
      p_UN <- 2*UN_k[1]*(p.a*(theta + (1-theta)*p.a)*(2*theta + 
              (1-theta)*p.a)*((1-theta)*p.diff) / 
                           ((1+theta)*(1+2*theta))) + 
              UN_k[2]*(p.a*(theta + (1-theta)*p.a)*((1-theta)*p.diff) / 
              (1+theta))
    } else{
    # no matching alleles
      # g2 homozygous (CASE 2)
      if (gt_pair[2,1] == gt_pair[2,2]){
        p_RE <- kap[1]*(p.a*(theta + (1-theta)*p.a)*
                (1-theta)*p.c*(theta + (1-theta)*p.c) / 
                            ((1+theta)*(1+2*theta)))
        p_UN <- UN_k[1]*(p.a*(theta + (1-theta)*p.a)*
                (1-theta)*p.c*(theta + (1-theta)*p.c) / 
                            ((1+theta)*(1+2*theta)))
      } else{
      # g2 heterozygous (CASE 4)
        p_RE <- 2*kap[1]*(p.a*(theta + (1-theta)*p.a)*
                (1-theta)*p.c*((1-theta)*p.d) / ((1+theta)*(1+2*theta)))
        p_UN <- 2*UN_k[1]*(p.a*(theta + (1-theta)*p.a)*(1-theta)*
                p.c*((1-theta)*p.d) / ((1+theta)*(1+2*theta)))
      }
    }
  } else{
  # g1 heterzygous
    # g1 = g2 (CASE 5)
    if (sum(gt_pair[2,] == gt_pair[1,]) == 2 | 
        sum(gt_pair[2,] == c(gt_pair[1,2], 
        gt_pair[1,1])) == 2){
      p_RE <- 4*kap[1]*(p.a*(1-theta)*p.b*(theta + 
              (1-theta)*p.a)*(theta + (1-theta)*p.b) / 
              ((1+theta)*(1+2*theta))) + 
              kap[2]*(p.a*(1-theta)*p.b*((theta + 
              (1-theta)*p.a) + (theta + (1-theta)*p.b)) / 
              (1+theta)) + 
              2*kap[3]*p.a*(1-theta)*p.b
      p_UN <- 4*UN_k[1]*(p.a*(1-theta)*p.b*(theta + 
              (1-theta)*p.a)*(theta + (1-theta)*p.b) / 
              ((1+theta)*(1+2*theta))) + 
              UN_k[2]*(p.a*(1-theta)*p.b*((theta + 
              (1-theta)*p.a) + (theta + (1-theta)*p.b)) / 
              (1+theta)) + 2*UN_k[3]*p.a*(1-theta)*p.b
    } else if(gt_pair[2,1] == gt_pair[1,1] | 
              gt_pair[2,1] == gt_pair[1,2] | 
              gt_pair[2,2] == gt_pair[1,1] | 
              gt_pair[2,2] == gt_pair[1,2]){
    # g1 and g2 heterozygous with one shared allele (CASE 6)
      # find which alleles matched
      if (gt_pair[2,1] == gt_pair[1,1]){
        p.same <- p.a
        p.diffg1 <- p.b
        p.diffg2 <- p.d
      } else if(gt_pair[2,1] == gt_pair[1,2]){
        p.same <- p.b
        p.diffg1 <- p.a
        p.diffg2 <- p.d
      } else if(gt_pair[2,2] == gt_pair[1,1]){
        p.same <- p.a
        p.diffg1 <- p.b
        p.diffg2 <- p.c
      } else{
        p.same <- p.b
        p.diffg1 <- p.a
        p.diffg2 <- p.c
      }
      p_RE <- 4*kap[1]*(p.same*(1-theta)*p.diffg1*(theta + 
              (1-theta)*p.same)*((1-theta)*p.diffg2) / 
              ((1+theta)*(1+2*theta))) + 
              kap[2]*(p.a*(1-theta)*p.diffg1*(1-theta)*p.diffg2 / 
              (1+theta))
      p_UN <- 4*UN_k[1]*(p.same*(1-theta)*p.diffg1*(theta + 
              (1-theta)*p.same)*((1-theta)*p.diffg2) / 
              ((1+theta)*(1+2*theta))) + 
              UN_k[2]*(p.a*(1-theta)*p.diffg1*(1-theta)*p.diffg2 / 
              (1+theta))
    } else{
    # all four alleles different (CASE 7)
      p_RE <- 4*kap[1]*(p.a*(1-theta)*p.b*(1-theta)*p.c*
              (1-theta)*p.d / ((1+theta)*(1+2*theta)))
      p_UN <- 4*UN_k[1]*(p.a*(1-theta)*p.b*(1-theta)*p.c*
              (1-theta)*p.d / ((1+theta)*(1+2*theta)))
    }
  }
  LR <- p_RE / p_UN
  return(LR)
}

### function to perform the pairwise calculations
run_calc <- function(pop_df, old_df, obs_df, theta){
  
  # get all possible combinations of tusks
  new_samples <- as.character(obs_df$Match.ID)
  obs_df$Match.ID <- NULL
  old_samples <- as.character(old_df$Match.ID)
  old_df$Match.ID <- NULL

  # get allele names (dropping -999 which corresponds to missing)
  pop_df[pop_df == -999] <- NA
  obs_df[obs_df == -999] <- NA
  old_df[old_df == -999] <- NA

  samples <- c(new_samples, old_samples)
  obs_df <- rbind(obs_df, old_df)
  
  sample_grid <- t(combn(samples, 2))
  index_grid <- t(combn(1:nrow(obs_df),2))
  sample_grid_filt <- matrix(, nrow = nrow(sample_grid), ncol=2)
  index_grid_filt <- matrix(, nrow = nrow(index_grid), ncol=2)
  for (i in 1:nrow(sample_grid)){
    if (sample_grid[i,1] %in% new_samples | 
        sample_grid[i,2] %in% new_samples){
      sample_grid_filt[i,] <- sample_grid[i,]
      index_grid_filt[i,] <- index_grid[i,]
    } 
  }
  incl_ind <- which(!is.na(sample_grid_filt[,1]))
  sample_grid_filt <- sample_grid_filt[incl_ind,]
  index_grid_filt <- index_grid_filt[incl_ind,]

  # add 4 NA column to fit the LR we'll calculate, as well as 1 for nloci
  sample_grid <- cbind(sample_grid_filt, 
                       matrix(, nrow=nrow(sample_grid_filt), ncol=5))
  index_grid <- index_grid_filt
  # get info from reference data
  # consider the full range of alleles from all loci in the obs data
  # this way we avoid having to update alleles on the fly
  # and only have to tweak the frequencies
  min_obs <- min(as.matrix(obs_df), na.rm=T)
  min_ref <- min(as.matrix(pop_df), na.rm=T)
  max_obs <- max(as.matrix(obs_df), na.rm=T)
  max_ref <- max(as.matrix(pop_df), na.rm=T)
  alleles <- seq(min(min_obs, min_ref), 
                 max(max_obs, max_ref))
  # get a matrix of allele frequencies using calc_afs function
  af_matrix <- apply(X = pop_df, MARGIN = 2, FUN = calc_afs, 
                     alleles)
  afs <- data.frame(af_matrix)

  # go through each pair of tusks
  for (i in 1:nrow(sample_grid)){
    pair <- index_grid[i,]
    # get gts
    gt1 <- obs_df[pair[1],]
    gt2 <- obs_df[pair[2],]
    # pick out only loci where both tusks have data
    gt1_obs <- which(!is.na(gt1))
    gt1_obs <- gt1_obs[gt1_obs %% 2 ==1]
    for (j in 1:length(gt1_obs)){
      if (is.na(gt1[gt1_obs[j]+1])){
        gt1_obs[j] <- NA
      }
    }
    gt1_obs <- gt1_obs[!is.na(gt1_obs)]
    gt2_obs <- which(!is.na(gt2))
    gt2_obs <- gt2_obs[gt2_obs %% 2 == 1]
    for (j in 1:length(gt2_obs)){
      if (is.na(gt2[gt2_obs[j]+1])){
        gt2_obs[j] <- NA
      }
    }
    gt2_obs <- gt2_obs[!is.na(gt2_obs)]
    both_obs <- intersect(gt1_obs, gt2_obs)
    gts <- rbind(gt1, gt2)
    gt_odd <- gts[,as.numeric(both_obs)] # allele 1
    gt_even <- gts[,as.numeric(both_obs + 1)] # allele 2
    # record number of loci
    nloci <- length(both_obs)
    sample_grid[i,7] <- nloci
    locus_names <- names(gts[both_obs])
    locus_indices <- (both_obs + 1)/2
    # make genotypes array
    pair <- array(, c(length(both_obs), 2, 3))
    pair[,,3] <- locus_names
    pair[,1,1] <- as.matrix(gt_odd[1,]) # individual 1, allele 1
    pair[,1,2] <- as.matrix(gt_even[1,]) # individual 1, allele 2
    pair[,2,1] <- as.matrix(gt_odd[2,]) # individual 2, allele 1
    pair[,2,2] <- as.matrix(gt_even[2,]) # individual 2, allele 2
    # now we need to get allele frequency df for this pair
    # which means introducing alleles that were not observed
    # in the reference
    afs_copy <- afs[,locus_names]
    for (j in 1:nloci){
      # observed alleles
      present_alleles <- as.vector(t(pair[j,,1:2]))
      present_alleles <- unique(as.numeric(present_alleles))
      # alleles in the ref
      ref_afs <- afs_copy[,j]
      ref_alleles <- alleles
      present_indices = which(ref_alleles %in% present_alleles)
      present_afs <- ref_afs[present_indices]
      # figure out alleles not in ref, introduce them
      # at freq theta, as per the 2018 Sci Advances paper
      missing <- present_indices[which(present_afs == 0)]
      if (length(missing) != 0){
        ref_afs <- ref_afs * (1-theta*length(missing))
        ref_afs[missing] <- theta
        afs_copy[,j] <- ref_afs
      }
    }
    # calculate the LRs for each relationship
    locus_FS_LRs <- apply(X = pair, MARGIN = 1, 
                          FUN = calc_kinship, FS_k, 
                          alleles, theta, afs_copy) 
    locus_HS_LRs <- apply(X = pair, MARGIN = 1, 
                          FUN = calc_kinship, HS_k, 
                          alleles, theta, afs_copy) 
    locus_PO_LRs <- apply(X = pair, MARGIN = 1, 
                          FUN = calc_kinship, PO_k, 
                          alleles, theta, afs_copy)
    locus_DM_LRs <- apply(X = pair, MARGIN = 1, 
                          FUN = calc_kinship, DM_k, 
                          alleles, theta, afs_copy)
    FS_LR <- prod(locus_FS_LRs)
    HS_LR <- prod(locus_HS_LRs)
    PO_LR <- prod(locus_PO_LRs)
    DM_LR <- prod(locus_DM_LRs)
    sample_grid[i,3] <- DM_LR
    sample_grid[i,4] <- PO_LR
    sample_grid[i,5] <- FS_LR
    sample_grid[i,6] <- HS_LR 
  }
  
  # organize the results
  dat <- data.frame(s1 = sample_grid[,1],
                    s2 = sample_grid[,2],
                    DM_LR = sample_grid[,3],
                    PO_LR = sample_grid[,4],
                    FS_LR = sample_grid[,5],
                    HS_LR = sample_grid[,6],
                    nloci = sample_grid[,7])
  return(dat)
}
