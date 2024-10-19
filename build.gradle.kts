plugins {
    kotlin("jvm") version "2.0.20"
}

group = "de.hackaton.2024"
version = "1.0-SNAPSHOT"

repositories {
    mavenLocal()
    mavenCentral()
}

dependencies {

    implementation(kotlin("stdlib"))

    implementation("io.kweb:kweb-core:1.4.12")

    // This (or another SLF4J binding) is required for Kweb to log errors


     // Basis-Module für Apache SIS

//    implementation("org.apache.sis.core:sis-utility:1.4")
    implementation("org.apache.sis.core:sis-metadata:1.4")
    implementation("org.apache.sis.core:sis-referencing:1.4")
    implementation("org.apache.sis.core:sis-referencing-by-identifiers:1.4")
    implementation("org.apache.sis.core:sis-feature:1.4")
    implementation("org.apache.sis.storage:sis-sqlstore:1.4")
    implementation("org.apache.sis.storage:sis-xmlstore:1.4")
    implementation("org.apache.sis.storage:sis-netcdf:1.4")
    implementation("org.apache.sis.storage:sis-geotiff:1.4")
    implementation("org.apache.sis.storage:sis-earth-observation:1.4")
//    implementation("org.apache.sis.profile:sis-japan-profil:1.4")
    implementation("org.apache.sis.cloud:sis-cloud-aws:1.4")
    implementation("org.apache.sis.application:sis-console:1.4")
    implementation("org.apache.sis.storage:sis-geotiff:1.4")
    implementation("org.apache.sis.non-free:sis-embedded-data:1.4")

    // Koordinten-Daten
    implementation("org.locationtech.jts:jts-core:1.18.2")

    // Logging
    implementation("org.slf4j:slf4j-simple:2.0.3")

    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
}