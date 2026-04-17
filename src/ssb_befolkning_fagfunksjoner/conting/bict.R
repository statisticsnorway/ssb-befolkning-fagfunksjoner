#------------------------------------------------------------
# Bayesian Imputation and Model Selection via RJ-MCMC
#------------------------------------------------------------
bict <- function(
    formula,
    data = NULL,
    n.sample,
    prior = "SBH",
    cens = NULL,
    start.formula = NULL,
    start.beta = NULL,
    start.sig = NULL,
    start.y0 = NULL,
    save = 0,
    name = NULL,
    null.move.prob = 0.5,
    a = 0.001,
    b = 0.001,
    progress = FALSE
) {

  #----------------------------------------------------------
  # 1. Input validation
  #----------------------------------------------------------
  if (n.sample <= 0) stop("n.sample must be positive")
  if (!prior %in% c("UIP", "SBH")) stop("prior not found")
  if (save < 0) stop("save must be non-negative")
  if (null.move.prob < 0 | null.move.prob > 1) {
    stop("null.move.prob must be between 0 and 1")
  }
  if ((a < 0 & a != -1) | b < 0) {
    stop("a and b must be non-negative")
  }

  # Start timing
  ptm <- proc.time()[3]

  #----------------------------------------------------------
  # 2. Data preparation
  #----------------------------------------------------------
  if (!is.null(data) && class(data) == "table") {
    data <- data.frame(data)
  }

  #----------------------------------------------------------
  # 3. File handling (if saving results)
  #----------------------------------------------------------
  if (save > 0) {

    # Default filenames
    prefix <- ifelse(is.null(name), "", name)

    files <- list(
      RJACC = paste0(prefix, "RJACC.txt"),
      MHACC = paste0(prefix, "MHACC.txt"),
      BETA  = paste0(prefix, "BETA.txt"),
      MODEL = paste0(prefix, "MODEL.txt"),
      SIG   = paste0(prefix, "SIG.txt"),
      Y0    = paste0(prefix, "Y0.txt")
    )

    # Check for existing files
    for (f in files) {
      if (file.exists(f)) {
        stop(paste("File already exists:", f))
      }
    }
  }

  #----------------------------------------------------------
  # 4. Prior setup
  #----------------------------------------------------------
  priornum <- ifelse(prior == "UIP", 1, 2)

  #----------------------------------------------------------
  # 5. Construct maximal model (design matrix)
  #----------------------------------------------------------
  options(contrasts = c("contr.sum", "contr.poly"), warn = -1)

  maximal_mod <- glm(
    formula = formula,
    data = data,
    method = "model.frame",
    na.action = na.pass,
    family = poisson,
    control = list(maxit = 1),
    x = TRUE,
    y = TRUE
  )

  options(contrasts = c("contr.treatment", "contr.poly"), warn = 0)

  #----------------------------------------------------------
  # 6. Handle missing and censored observations
  #----------------------------------------------------------
  missing1 <- which(is.na(maximal_mod[, 1]))

  data <- maximal_mod
  data[missing1, 1] <- 0  # Replace missing response with 0

  missing2 <- if (!is.null(cens)) cens else integer(0)
  missing  <- c(missing1, missing2)

  missing_details  <- data[missing1, -1]
  censored_details <- data[missing2, -1]

  #----------------------------------------------------------
  # 7. Re-fit maximal model (with modified data)
  #----------------------------------------------------------
  options(contrasts = c("contr.sum", "contr.poly"), warn = -1)

  maximal.mod <- glm(
    formula = formula,
    data = data,
    family = poisson,
    control = list(maxit = 1),
    x = TRUE,
    y = TRUE
  )

  options(contrasts = c("contr.treatment", "contr.poly"), warn = 0)

  big.X <- maximal.mod$x
  y     <- maximal.mod$y
  n     <- nrow(big.X)

  #----------------------------------------------------------
  # 8. Compute information matrix (IP)
  #----------------------------------------------------------
  IP <- t(big.X) %*% big.X / n
  IP[, 1] <- 0
  IP[1, ] <- 0

  #----------------------------------------------------------
  # 9. Initial parameter estimates
  #----------------------------------------------------------
  bmod <- beta_mode(
    X = big.X[-missing, ],
    y = y[-missing],
    prior = prior,
    IP = IP,
    a = a,
    b = b
  )

  eta.hat <- as.vector(big.X %*% matrix(bmod, ncol = 1))

  #----------------------------------------------------------
  # 10. Initialize model parameters
  #----------------------------------------------------------
  start.index <- if (is.null(start.formula)) {
    rep(1, ncol(big.X))
  } else {
    formula2index(big.X = big.X, formula = start.formula, data = data)
  }

  if (is.null(start.beta)) {
    start.beta <- bmod[start.index == 1]
  }

  if (is.null(start.sig)) {
    start.sig <- 1
  }

  if (is.null(start.y0)) {
    start.y0 <- round(exp(eta.hat[missing]))
  }

  #----------------------------------------------------------
  # 11. Run RJ-MCMC algorithm
  #----------------------------------------------------------
  runit <- bict.fit(
    priornum = priornum,
    missing1 = missing1,
    missing2 = missing2,
    maximal.mod = maximal.mod,
    IP = IP,
    eta.hat = eta.hat,
    ini.index = start.index,
    ini.beta = start.beta,
    ini.sig = start.sig,
    ini.y0 = start.y0,
    iters = n.sample,
    save = save,
    name = name,
    null.move.prob = null.move.prob,
    a = a,
    b = b,
    progress = progress
  )

  # Extract results
  BETA  <- runit$BETA
  MODEL <- runit$MODEL
  SIG   <- runit$SIG
  Y0    <- runit$Y0
  rj_acc <- runit$rj_acc
  mh_acc <- runit$mh_acc

  #----------------------------------------------------------
  # 12. Reload results from files (if saved)
  #----------------------------------------------------------
  if (save > 0) {
    BETA  <- read.matrix(files$BETA, header = FALSE)
    SIG   <- read.matrix(files$SIG, header = FALSE)
    Y0    <- matrix(read.matrix(files$Y0, header = FALSE), nrow = length(SIG))
    MODEL <- as.character(read.table(files$MODEL)[, 1])
    rj_acc <- read.matrix(files$RJACC, header = FALSE)
    mh_acc <- read.matrix(files$MHACC, header = FALSE)
  }

  #----------------------------------------------------------
  # 13. Final output
  #----------------------------------------------------------
  time <- proc.time()[3] - ptm

  est <- list(
    BETA = BETA,
    MODEL = MODEL,
    SIG = SIG,
    Y0 = Y0,
    missing1 = missing1,
    missing2 = missing2,
    missing_details = missing_details,
    censored_details = censored_details,
    rj_acc = rj_acc,
    mh_acc = mh_acc,
    priornum = priornum,
    maximal.mod = maximal.mod,
    IP = IP,
    eta.hat = eta.hat,
    save = save,
    name = name,
    null.move.prob = null.move.prob,
    time = time,
    a = a,
    b = b
  )

  class(est) <- "bict"

  return(est)
}
