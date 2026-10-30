Feature: HU01 - Registro y alta de wallet (MVP básico funcional)
  # Trazabilidad: CA-02, CA-03, CA-04 (openspec/changes/onboarding-wallet-registration)
  # API bajo prueba: Wallet Onboarding Service (src/main.py), que a su vez integra el
  # mock real documentado en client/openapi/kyc-wallet-mock.yaml.

  Background:
    * url baseUrl
    * def randomSuffix = function(){ return java.util.UUID.randomUUID().toString().substring(0,6) }

  @CA-03 @APPROVED
  Scenario: Registro feliz crea una wallet ACTIVE_BASIC con saldo cero (escenario APPROVED)
    * def uniqueUser = 'k_ok_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Prueba",
      "apellidoPaterno": "Delgado",
      "apellidoMaterno": "Soto",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-approved"
    }
    """
    When method post
    Then status 201
    And match response.kycStatus == 'ACTIVE'
    And match response.appTier == 'ACTIVE_BASIC'
    And match response.balance == 0
    And match response.currency == 'PEN'
    And match response.walletId == '#string'
    * def walletId = response.walletId

    Given path '/wallets/' + walletId
    When method get
    Then status 200
    And match response.kycStatus == 'ACTIVE'
    And match response.limits.perOperation == 2000
    And match response.limits.dailyRemaining == 6000

  @CA-04 @MANUAL_REVIEW
  Scenario: Escenario MANUAL_REVIEW deja la wallet en PENDING y abre un caso de soporte
    * def uniqueUser = 'k_pend_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Revision",
      "apellidoPaterno": "Vargas",
      "apellidoMaterno": "Nina",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-pending",
      "testScenario": "MANUAL_REVIEW"
    }
    """
    When method post
    Then status 201
    And match response.kycStatus == 'PENDING'
    And match response.appTier == '#null'
    And match response.supportCase.status == 'OPEN'

  @CA-04 @REJECTED
  Scenario: Escenario REJECTED bloquea la cuenta y los pagos devuelven 409
    * def uniqueUser = 'k_rej_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Rechazo",
      "apellidoPaterno": "Quispe",
      "apellidoMaterno": "Flores",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-rejected",
      "testScenario": "REJECTED"
    }
    """
    When method post
    Then status 201
    And match response.kycStatus == 'REJECTED'
    * def walletId = response.walletId

    Given path '/wallets/' + walletId + '/payments'
    And request { "amount": 500 }
    When method post
    Then status 409
    And match response.detail.code == 'WALLET_NOT_OPERATIONAL'

  @CA-04 @UNAVAILABLE
  Scenario: Escenario UNAVAILABLE no crea wallet y responde 503
    * def uniqueUser = 'k_unav_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Indisponible",
      "apellidoPaterno": "Rojas",
      "apellidoMaterno": "Paredes",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-unavailable",
      "testScenario": "UNAVAILABLE"
    }
    """
    When method post
    Then status 503

  @CA-02
  Scenario: El registro rechaza nombres con caracteres no alfabéticos
    * def uniqueUser = 'k_bad_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Juan3",
      "apellidoPaterno": "Perez",
      "apellidoMaterno": "Gomez",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-badname"
    }
    """
    When method post
    Then status 422

  @CA-02
  Scenario: El nombre de usuario repetido no está disponible y se informa el conflicto
    * def uniqueUser = 'k_dup_' + randomSuffix()
    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Original",
      "apellidoPaterno": "Mamani",
      "apellidoMaterno": "Ccopa",
      "username": "#(uniqueUser)",
      "password": "Karate#2026Pwd",
      "flowId": "karate-flow-dup-1"
    }
    """
    When method post
    Then status 201

    Given path '/registrations'
    And request
    """
    {
      "nombres": "Karate Duplicado",
      "apellidoPaterno": "Mamani",
      "apellidoMaterno": "Ccopa",
      "username": "#(uniqueUser)",
      "password": "OtraClave#2026",
      "flowId": "karate-flow-dup-2"
    }
    """
    When method post
    Then status 400
    And match response.detail.code == 'USERNAME_TAKEN'
